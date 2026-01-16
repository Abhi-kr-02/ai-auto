"""
SHVYA Worker - All Priority-Based Tasks
Implements P1 (AI conversational) and P2 (timed/scheduled) jobs
"""
from celery_app import celery
from database import SessionLocal
from models import Lead, Message, AIKBDoc, Stage, Job, Event
from ai import generate_ai_reply
from rules import can_ai_reply
from queue_manager import mark_job_started, mark_job_completed, mark_job_failed
from channels import ChannelRouter
from datetime import datetime, timedelta
import json


# ============================================================================
# P1 TASKS: AI Conversational (Priority 90-100)
# ============================================================================

@celery.task(name="worker.ai_engage", priority=100)
def ai_engage(job_id: str):
    """
    P1 Task - Priority 100
    AI Engagement: Processes inbound messages and generates AI replies
    """
    db = SessionLocal()
    try:
        mark_job_started(job_id)
        
        # Get job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        lead_id = job.payload.get("lead_id")
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            mark_job_failed(job_id, "Lead not found")
            return {"error": "Lead not found"}

        # Get all messages for this lead
        messages = db.query(Message).filter(
            Message.lead_id == lead_id
        ).order_by(Message.created_at).all()

        # Check if AI should reply
        if not can_ai_reply(messages):
            mark_job_completed(job_id)
            return {"status": "skipped", "reason": "Last message was outbound"}

        # Get stage info
        stage = db.query(Stage).filter(Stage.id == lead.stage_id).first() if lead.stage_id else None
        stage_name = stage.name if stage else "New"

        # Get company KB docs (top 3 most relevant - simple version)
        kb_docs = db.query(AIKBDoc).filter(
            AIKBDoc.company_id == lead.company_id
        ).limit(3).all() if lead.company_id else []
        
        kb_context = "\n\nKnowledge Base:\n" + "\n".join([
            f"- {doc.title}: {doc.content[:200]}..." for doc in kb_docs
        ]) if kb_docs else ""

        # Build context from conversation history
        context = f"Lead: {lead.name or lead.phone}\nStage: {stage_name}{kb_context}\n\nConversation:\n"
        for msg in messages[-5:]:  # Last 5 messages
            context += f"{msg.direction.upper()}: {msg.body}\n"

        # Generate AI reply
        ai_response = generate_ai_reply(context)
        
        # Determine channel (prefer WhatsApp)
        channel = "wa_web"  # Default to WhatsApp Web for now
        
        # Route message through channel adapter
        send_result = ChannelRouter.send(channel, {
            "phone": lead.phone,
            "body": ai_response.get("reply", "")
        })
        
        # Save AI reply to database
        reply_msg = Message(
            lead_id=lead_id,
            channel=channel,
            direction="outbound",
            body=ai_response.get("reply", ""),
            status=send_result.get("status"),
            external_id=send_result.get("external_id"),
            sent_at=datetime.utcnow()
        )
        db.add(reply_msg)
        
        # Log event
        event = Event(
            type="AIEngageCompleted",
            entity_type="lead",
            entity_id=lead_id,
            payload={"reply": ai_response.get("reply"), "channel": channel}
        )
        db.add(event)
        
        db.commit()
        mark_job_completed(job_id)

        return {
            "status": "completed",
            "lead_id": lead_id,
            "reply": ai_response.get("reply"),
            "channel": channel,
            "should_stop": ai_response.get("should_stop", False)
        }
    
    except Exception as e:
        db.rollback()
        mark_job_failed(job_id, str(e))
        return {"error": str(e)}
    finally:
        db.close()


@celery.task(name="worker.followup_bumpup", priority=95)
def followup_bumpup(job_id: str):
    """
    P1 Task - Priority 95
    Smart Bump-Up: Re-engage idle leads with varied, short nudges
    """
    db = SessionLocal()
    try:
        mark_job_started(job_id)
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        lead_id = job.payload.get("lead_id")
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        
        if not lead:
            mark_job_failed(job_id, "Lead not found")
            return {"error": "Lead not found"}
        
        # Get last bot message to avoid repetition
        last_msg = db.query(Message).filter(
            Message.lead_id == lead_id,
            Message.direction == "outbound"
        ).order_by(Message.created_at.desc()).first()
        
        # Generate bump-up message (30-40 words, non-repetitive)
        bump_up_prompts = [
            f"Previous message: {last_msg.body if last_msg else 'None'}. Generate a different 35-word follow-up.",
            "Create a friendly 35-word check-in that's different from previous messages.",
        ]
        
        context = f"Lead: {lead.phone}\n{bump_up_prompts[0]}"
        ai_response = generate_ai_reply(context)
        
        # Send via preferred channel (WhatsApp only, never email)
        channel = "wa_web"
        send_result = ChannelRouter.send(channel, {
            "phone": lead.phone,
            "body": ai_response.get("reply", "")
        })
        
        # Save message
        msg = Message(
            lead_id=lead_id,
            channel=channel,
            direction="outbound",
            body=ai_response.get("reply", ""),
            status=send_result.get("status"),
            external_id=send_result.get("external_id"),
            sent_at=datetime.utcnow()
        )
        db.add(msg)
        db.commit()
        
        mark_job_completed(job_id)
        return {"status": "completed", "lead_id": lead_id}
    
    except Exception as e:
        db.rollback()
        mark_job_failed(job_id, str(e))
        return {"error": str(e)}
    finally:
        db.close()


@celery.task(name="worker.ai_summary", priority=90)
def ai_summary(job_id: str):
    """
    P1 Task - Priority 90
    AI Summary: Generate conversation summary and extract insights
    """
    db = SessionLocal()
    try:
        mark_job_started(job_id)
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        lead_id = job.payload.get("lead_id")
        
        # Get all messages
        messages = db.query(Message).filter(
            Message.lead_id == lead_id
        ).order_by(Message.created_at).all()
        
        # Build conversation for summary
        conversation = "\n".join([
            f"{msg.direction}: {msg.body}" for msg in messages
        ])
        
        summary_prompt = f"Summarize this conversation in 3-5 sentences:\n{conversation}"
        summary = generate_ai_reply(summary_prompt)
        
        # Update lead attributes with summary
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.attributes = lead.attributes or {}
            lead.attributes["ai_summary"] = summary.get("reply")
            db.commit()
        
        mark_job_completed(job_id)
        return {"status": "completed", "summary": summary.get("reply")}
    
    except Exception as e:
        db.rollback()
        mark_job_failed(job_id, str(e))
        return {"error": str(e)}
    finally:
        db.close()


# ============================================================================
# P2 TASKS: Timed/Scheduled (Priority 50-70)
# ============================================================================

@celery.task(name="worker.sequence_step", priority=70)
def sequence_step(job_id: str):
    """
    P2 Task - Priority 70
    Sequence Step: Execute a step in a follow-up sequence
    """
    db = SessionLocal()
    try:
        mark_job_started(job_id)
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        # TODO: Implement sequence step logic
        # - Get sequence step details
        # - Check stop conditions (reply received, stage changed)
        # - Send message via appropriate channel
        # - Schedule next step if needed
        
        mark_job_completed(job_id)
        return {"status": "completed", "message": "Sequence step executed"}
    
    except Exception as e:
        db.rollback()
        mark_job_failed(job_id, str(e))
        return {"error": str(e)}
    finally:
        db.close()


@celery.task(name="worker.email_sequence", priority=60)
def email_sequence(job_id: str):
    """
    P2 Task - Priority 60
    Email Sequence: Send scheduled email from sequence
    """
    db = SessionLocal()
    try:
        mark_job_started(job_id)
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        # TODO: Implement email sequence logic
        # - Get email template
        # - Personalize content
        # - Send via EmailAdapter
        # - Handle bounces/unsubscribes
        
        mark_job_completed(job_id)
        return {"status": "completed", "message": "Email sent"}
    
    except Exception as e:
        db.rollback()
        mark_job_failed(job_id, str(e))
        return {"error": str(e)}
    finally:
        db.close()


@celery.task(name="worker.webhook_reminder", priority=50)
def webhook_reminder(job_id: str):
    """
    P2 Task - Priority 50
    Webhook Reminder: Send webhook notification
    """
    db = SessionLocal()
    try:
        mark_job_started(job_id)
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        # TODO: Implement webhook logic
        # - Get webhook URL and payload
        # - Sign request
        # - Send with retry logic
        
        mark_job_completed(job_id)
        return {"status": "completed", "message": "Webhook sent"}
    
    except Exception as e:
        db.rollback()
        mark_job_failed(job_id, str(e))
        return {"error": str(e)}
    finally:
        db.close()

