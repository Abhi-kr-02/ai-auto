from fastapi import FastAPI
from app.schemas import InboundMessage
from app.database import SessionLocal, engine
from app.models import Base, Lead, Message
from worker import ai_engage

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/inbound-message")
def inbound_message(data: InboundMessage):
    db = SessionLocal()

    lead = db.query(Lead).filter(Lead.phone == data.phone).first()
    if not lead:
        lead = Lead(phone=data.phone)
        db.add(lead)
        db.commit()
        db.refresh(lead)

    msg = Message(
        lead_id=lead.id,
        direction="inbound",
        body=data.text
    )
    db.add(msg)
    db.commit()

    ai_engage.delay(lead.id)

    return {"status": "queued"}
