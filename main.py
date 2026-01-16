from fastapi import FastAPI, HTTPException
from schemas import InboundMessage
from database import SessionLocal, engine
from models import Base, Lead, Message, Event, Company, Pipeline, Stage
from queue_manager import enqueue_job
import uuid

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SHVYA AI Auto API",
    description="AI-powered sales engagement platform with priority-based queue system",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "SHVYA AI Auto API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "inbound_message": "/inbound-message",
            "queue_stats": "/queue/stats"
        }
    }

@app.post("/inbound-message")
def inbound_message(data: InboundMessage):
    """
    Handle inbound messages from any channel
    Creates/updates lead, logs message, enqueues AI engagement
    """
    db = SessionLocal()
    try:
        # Find or create lead
        lead = db.query(Lead).filter(Lead.phone == data.phone_number).first()
        if not lead:
            # Get default company and pipeline (for now, use first available)
            company = db.query(Company).first()
            if not company:
                # Create default company
                company = Company(
                    id=str(uuid.uuid4()),
                    name="Default Company",
                    timezone="UTC"
                )
                db.add(company)
                db.flush()
            
            pipeline = db.query(Pipeline).filter(
                Pipeline.company_id == company.id
            ).first()
            if not pipeline:
                # Create default pipeline
                pipeline = Pipeline(
                    id=str(uuid.uuid4()),
                    company_id=company.id,
                    name="Default Pipeline",
                    is_default=True
                )
                db.add(pipeline)
                db.flush()
            
            # Get "New" stage
            stage = db.query(Stage).filter(
                Stage.pipeline_id == pipeline.id,
                Stage.name == "New"
            ).first()
            if not stage:
                # Create default stages
                stages = [
                    Stage(id=str(uuid.uuid4()), pipeline_id=pipeline.id, name="New", order=1),
                    Stage(id=str(uuid.uuid4()), pipeline_id=pipeline.id, name="Qualified", order=2),
                    Stage(id=str(uuid.uuid4()), pipeline_id=pipeline.id, name="Converted", order=3),
                ]
                db.add_all(stages)
                db.flush()
                stage = stages[0]
            
            # Create lead
            lead = Lead(
                id=str(uuid.uuid4()),
                company_id=company.id,
                pipeline_id=pipeline.id,
                stage_id=stage.id,
                phone=data.phone_number,
                name=data.contact_name,
                source="api"
            )
            db.add(lead)
            db.flush()
            
            # Log LeadCreated event
            event = Event(
                type="LeadCreated",
                entity_type="lead",
                entity_id=lead.id,
                payload={"phone": data.phone_number, "contact_name": data.contact_name, "source": "api"}
            )
            db.add(event)

        # Create inbound message
        msg = Message(
            id=str(uuid.uuid4()),
            lead_id=lead.id,
            channel=data.channel,
            direction="inbound",
            body=data.message_text,
            status="received"
        )
        db.add(msg)
        
        # Log InboundMessageReceived event
        event = Event(
            type="InboundMessageReceived",
            entity_type="message",
            entity_id=msg.id,
            payload={"lead_id": lead.id, "body": data.message_text, "channel": data.channel}
        )
        db.add(event)
        
        db.commit()
        db.refresh(lead)
        db.refresh(msg)

        # Enqueue AI engagement (P1 - Priority 100)
        job_id = enqueue_job(
            job_type="ai.engage",
            payload={"lead_id": lead.id},
            idempotency_key=f"ai_engage_{lead.id}_{msg.id}"
        )

        return {
            "status": "queued",
            "lead_id": lead.id,
            "message_id": msg.id,
            "job_id": job_id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/queue/stats")
def queue_stats():
    """Get queue statistics"""
    from queue_manager import get_queue_stats
    return get_queue_stats()


@app.post("/admin/dlq/replay")
def replay_dlq(limit: int = 10):
    """Admin endpoint to replay jobs from Dead Letter Queue"""
    from queue_manager import replay_dlq_jobs
    replayed = replay_dlq_jobs(limit)
    return {"replayed": replayed, "message": f"Replayed {replayed} jobs from DLQ"}
