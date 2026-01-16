from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, Text, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid

# ============================================================================
# PHASE 1: CORE TABLES - Companies, Users, Pipelines, Stages
# ============================================================================

class Company(Base):
    __tablename__ = "companies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    timezone = Column(String, default="UTC")
    plan = Column(String, default="free")  # free, pro, enterprise
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Company card for AI context
    company_card = Column(JSON)  # {name, tone, usp, legal_lines}

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"))
    name = Column(String)
    role = Column(String)  # admin, agent, supervisor
    email = Column(String)
    phone = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Pipeline(Base):
    __tablename__ = "pipelines"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"))
    name = Column(String)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Stage(Base):
    __tablename__ = "stages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id = Column(String, ForeignKey("pipelines.id"))
    name = Column(String)  # New, Qualified, Nurture, Converted, Lost
    order = Column(Integer)
    visible = Column(Boolean, default=True)
    ai_on = Column(Boolean, default=True)
    config = Column(JSON)  # Stage-specific configuration

# ============================================================================
# LEADS & CONTACTS
# ============================================================================

class Lead(Base):
    __tablename__ = "leads"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"))
    pipeline_id = Column(String, ForeignKey("pipelines.id"))
    stage_id = Column(String, ForeignKey("stages.id"))
    source = Column(String)  # google_ads, facebook, whatsapp, etc.
    name = Column(String)
    phone = Column(String)
    email = Column(String)
    attributes = Column(JSON)  # Custom attributes
    status = Column(String, default="active")  # active, inactive, archived
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_company_phone', 'company_id', 'phone', unique=True),
    )

class LeadContact(Base):
    __tablename__ = "lead_contacts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"))
    channel = Column(String)  # wa_web, wa_cloud, email, sms
    handle = Column(String)  # phone number, email address
    verified = Column(Boolean, default=False)

# ============================================================================
# MESSAGES & EVENTS
# ============================================================================

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"))
    channel = Column(String)  # wa_web, wa_cloud, email
    direction = Column(String)  # inbound, outbound
    template_id = Column(String, ForeignKey("templates.id"), nullable=True)
    body = Column(Text)
    status = Column(String)  # queued, sent, delivered, read, failed
    external_id = Column(String, unique=True, nullable=True)  # For idempotency
    error = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_external_id', 'external_id', unique=True),
    )

class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String)  # LeadCreated, StageChanged, MessageSent, AIEngaged
    entity_type = Column(String)  # lead, message, stage
    entity_id = Column(String)
    payload = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_entity', 'entity_type', 'entity_id'),
    )

# ============================================================================
# SEQUENCES & TEMPLATES
# ============================================================================

class Sequence(Base):
    __tablename__ = "sequences"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"))
    name = Column(String)
    channel = Column(String)  # wa_web, wa_cloud, email
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SequenceStep(Base):
    __tablename__ = "sequence_steps"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence_id = Column(String, ForeignKey("sequences.id"))
    step_no = Column(Integer)
    send_policy = Column(String)  # immediate, time, delay
    time_window = Column(String, nullable=True)  # AM, PM
    delay_value = Column(Integer, nullable=True)
    delay_unit = Column(String, nullable=True)  # min, hour, day
    template_id = Column(String, ForeignKey("templates.id"))
    ai_flag = Column(Boolean, default=False)
    stop_on_reply = Column(Boolean, default=True)

class Template(Base):
    __tablename__ = "templates"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"))
    channel = Column(String)  # wa_cloud, email
    name = Column(String)
    body = Column(Text)
    params = Column(JSON)  # Template variables
    meta = Column(JSON)  # Channel-specific metadata
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ============================================================================
# AI MODELS & KNOWLEDGE BASE
# ============================================================================

class AIModel(Base):
    __tablename__ = "ai_models"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"))
    provider = Column(String, default="openai")  # openai, anthropic
    model_name = Column(String, default="gpt-4o-mini")
    temperature = Column(Float, default=0.4)
    top_p = Column(Float, default=1.0)
    max_tokens = Column(Integer, default=500)
    system_prompt = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AIKBDoc(Base):
    __tablename__ = "ai_kb_docs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"))
    title = Column(String)
    content = Column(Text)
    # embedding = Column(Vector(1536))  # Will need pgvector extension
    embedding = Column(JSON, nullable=True)  # Temporary: store as JSON array
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AISession(Base):
    __tablename__ = "ai_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String, ForeignKey("leads.id"))
    model_id = Column(String, ForeignKey("ai_models.id"))
    memory = Column(JSON)  # Conversation context
    last_turn_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ============================================================================
# QUEUE & JOB TRACKING (Phase 2)
# ============================================================================

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = Column(String)  # ai.engage, followup.bumpup, sequence.step, etc.
    priority = Column(Integer)  # P1: 90-100, P2: 50-70
    payload = Column(JSON)
    status = Column(String, default="queued")  # queued, processing, completed, failed, dlq
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    error = Column(Text, nullable=True)
    idempotency_key = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_status_priority', 'status', 'priority'),
    )

# ============================================================================
# REPORTS CACHE
# ============================================================================

class ReportCache(Base):
    __tablename__ = "reports_cache"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"))
    slug = Column(String)
    json = Column(JSON)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
