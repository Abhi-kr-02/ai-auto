from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from .database import Base

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True)
    phone = Column(String, unique=True)
    stage = Column(String, default="New")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    direction = Column(String)  # inbound / outbound
    body = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
