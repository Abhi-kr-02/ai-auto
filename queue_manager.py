"""
Phase 2: Priority-based Queue Manager
Handles job priorities, DLQ, idempotency, and retry logic
"""
from celery_app import celery
from database import SessionLocal
from models import Job
from datetime import datetime
import json

# ============================================================================
# JOB PRIORITIES (Non-Negotiable from SHVYA Guide)
# ============================================================================
PRIORITIES = {
    # P1: AI conversational (highest priority)
    "ai.engage": 100,
    "followup.bumpup": 95,
    "ai.summary": 90,
    
    # P2: Timed/scheduled (lower priority)
    "sequence.step": 70,
    "email.sequence": 60,
    "webhook.reminder": 50,
}

# ============================================================================
# QUEUE HELPER FUNCTIONS
# ============================================================================

def enqueue_job(job_type: str, payload: dict, idempotency_key: str = None):
    """
    Central enqueue helper - enforces priorities and idempotency
    
    Args:
        job_type: Type of job (must be in PRIORITIES)
        payload: Job data
        idempotency_key: Optional key for deduplication
    
    Returns:
        Job ID or None if duplicate
    """
    db = SessionLocal()
    try:
        # Check idempotency
        if idempotency_key:
            existing = db.query(Job).filter(
                Job.idempotency_key == idempotency_key
            ).first()
            if existing:
                return None  # Job already exists
        
        # Get priority
        priority = PRIORITIES.get(job_type, 50)
        
        # Create job record
        job = Job(
            job_type=job_type,
            priority=priority,
            payload=payload,
            idempotency_key=idempotency_key,
            status="queued"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Enqueue to Celery with priority
        task_name = f"worker.{job_type.replace('.', '_')}"
        celery.send_task(
            task_name,
            args=[job.id],
            priority=priority,
            kwargs={"job_id": job.id}
        )
        
        return job.id
    
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def mark_job_started(job_id: str):
    """Mark job as processing"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "processing"
            job.started_at = datetime.utcnow()
            job.attempts += 1
            db.commit()
    finally:
        db.close()


def mark_job_completed(job_id: str):
    """Mark job as completed"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def mark_job_failed(job_id: str, error: str):
    """Mark job as failed or move to DLQ"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.error = error
            
            if job.attempts >= job.max_attempts:
                # Move to Dead Letter Queue
                job.status = "dlq"
            else:
                # Retry with exponential backoff
                job.status = "queued"
                backoff_delays = [5, 20, 60, 180, 600]  # seconds
                delay = backoff_delays[min(job.attempts - 1, len(backoff_delays) - 1)]
                
                # Re-enqueue with delay
                task_name = f"worker.{job.job_type.replace('.', '_')}"
                celery.send_task(
                    task_name,
                    args=[job.id],
                    priority=job.priority,
                    countdown=delay
                )
            
            db.commit()
    finally:
        db.close()


def replay_dlq_jobs(limit: int = 10):
    """
    Admin function to replay jobs from DLQ
    Returns: Number of jobs replayed
    """
    db = SessionLocal()
    try:
        dlq_jobs = db.query(Job).filter(
            Job.status == "dlq"
        ).limit(limit).all()
        
        replayed = 0
        for job in dlq_jobs:
            # Reset job
            job.status = "queued"
            job.attempts = 0
            job.error = None
            
            # Re-enqueue
            task_name = f"worker.{job.job_type.replace('.', '_')}"
            celery.send_task(
                task_name,
                args=[job.id],
                priority=job.priority
            )
            replayed += 1
        
        db.commit()
        return replayed
    
    finally:
        db.close()


def get_queue_stats():
    """Get queue statistics"""
    db = SessionLocal()
    try:
        stats = {
            "queued": db.query(Job).filter(Job.status == "queued").count(),
            "processing": db.query(Job).filter(Job.status == "processing").count(),
            "completed": db.query(Job).filter(Job.status == "completed").count(),
            "failed": db.query(Job).filter(Job.status == "failed").count(),
            "dlq": db.query(Job).filter(Job.status == "dlq").count(),
        }
        return stats
    finally:
        db.close()
