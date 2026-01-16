# Developer Guide - SHVYA AI Auto

Quick reference for developers to understand the codebase structure and make updates.

---

## 📁 File Structure Overview

```
ai-auto/
├── main.py              # FastAPI web server & REST endpoints
├── worker.py            # Celery background tasks
├── models.py            # Database schema (16 tables)
├── database.py          # Database connection & session
├── schemas.py           # Pydantic request/response models
├── queue_manager.py     # Priority queue & job management
├── channels.py          # Multi-channel message routing
├── celery_app.py        # Celery configuration
├── ai.py                # OpenAI API integration
├── rules.py             # Business logic & rules
├── start.ps1            # Start API server script
├── start-worker.ps1     # Start Celery worker script
├── start-all.ps1        # Start all services script
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # PostgreSQL + Redis containers
└── .env                 # Environment variables (create from env.example)
```

---

## 🔧 Core Files Explained

### main.py - API Server
**What it does**: REST API endpoints for receiving messages and monitoring

**Key endpoints**:
```python
POST /inbound-message     # Receive messages from any channel
GET  /queue/stats         # Monitor queue health
POST /admin/dlq/replay    # Replay failed jobs
```

**Auto-creation logic**:
- Creates Company if missing
- Creates Pipeline with 5 stages (New, Contacted, Qualified, Proposal, Closed)
- Creates/updates Lead records
- Logs all events for audit trail

**When to modify**:
- Adding new API endpoints
- Changing auto-creation behavior
- Adding middleware or authentication
- Modifying response formats

**Dependencies**: `schemas`, `database`, `models`, `queue_manager`

---

### worker.py - Background Tasks
**What it does**: Processes jobs from the queue (AI responses, follow-ups, etc.)

**6 Tasks implemented**:
```python
@celery_app.task(priority=100)
def ai_engage(lead_id, message_id):
    # Generate AI response to inbound message
    # Uses: OpenAI API, KB search, channel routing
    
@celery_app.task(priority=95)
def followup_bumpup(lead_id):
    # Send smart follow-up to re-engage cold leads
    
@celery_app.task(priority=90)
def ai_summary(lead_id):
    # Summarize conversation and store in lead attributes
    
@celery_app.task(priority=70)
def sequence_step(sequence_id, lead_id):
    # TODO: Execute next step in automation sequence
    
@celery_app.task(priority=60)
def email_sequence(campaign_id, lead_id):
    # TODO: Send scheduled email in campaign
    
@celery_app.task(priority=50)
def webhook_reminder(webhook_id, payload):
    # TODO: Send webhook notification to external system
```

**When to modify**:
- Adding new background tasks
- Changing task priorities
- Modifying AI behavior
- Adding new integrations

**Dependencies**: `celery_app`, `database`, `models`, `ai`, `rules`, `queue_manager`, `channels`

---

### models.py - Database Schema
**What it does**: Defines all 16 database tables with relationships

**Table categories**:

**Core Business**:
- `Company` - Multi-tenant organizations
- `User` - Team members
- `Pipeline` - Sales pipeline definitions
- `Stage` - Pipeline stages

**Lead Management**:
- `Lead` - Contact records with JSON attributes
- `LeadContact` - Multi-channel contact info (phone, email, etc.)
- `Message` - Conversation history

**Automation**:
- `Sequence` - Automation workflows
- `SequenceStep` - Individual actions in sequence
- `Template` - Message templates

**AI System**:
- `AIModel` - AI configuration per company
- `AIKBDoc` - Knowledge base documents
- `AISession` - Conversation context tracking

**Infrastructure**:
- `Job` - Queue job records
- `Event` - Audit trail (event sourcing)
- `ReportCache` - Pre-computed analytics

**When to modify**:
- Adding new tables or columns
- Changing relationships
- Adding indexes for performance
- Modifying JSON attribute structure

**Key patterns**:
```python
# UUID primary keys
id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

# Timestamps on every table
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# JSON columns for flexibility
attributes = Column(JSON, default=dict)
```

---

### database.py - Database Connection
**What it does**: Manages database connection and session lifecycle

**Key features**:
- SQLite fallback for development (no Docker needed)
- PostgreSQL for production
- Connection pooling
- Session management

**Configuration**:
```python
# Via .env file
DATABASE_URL=sqlite:///./test.db  # Development
# or
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname  # Production
```

**When to modify**:
- Changing database engine
- Modifying connection pool settings
- Adding database middleware

---

### queue_manager.py - Priority Queue
**What it does**: Manages job queue with priorities, retries, and DLQ

**Key functions**:
```python
enqueue_job(task_name, task_params, idempotency_key=None, priority=None)
    # Creates job record, prevents duplicates, enqueues to Celery
    
mark_job_started(job_id)
    # Updates status to 'processing'
    
mark_job_completed(job_id, result=None)
    # Updates status to 'completed'
    
mark_job_failed(job_id, error_message)
    # Handles retries or moves to DLQ
    
replay_dlq_jobs(max_jobs=10)
    # Re-enqueues failed jobs from DLQ
    
get_queue_stats()
    # Returns job counts by status
```

**Priority mapping**:
```python
PRIORITIES = {
    "ai.engage": 100,         # P1 - Conversational
    "followup.bumpup": 95,    # P1
    "ai.summary": 90,         # P1
    "sequence.step": 70,      # P2 - Scheduled
    "email.sequence": 60,     # P2
    "webhook.reminder": 50,   # P2
}
```

**Retry schedule**: 5s → 20s → 60s → 3m → 10m → DLQ

**When to modify**:
- Adding new job types with priorities
- Changing retry logic
- Modifying DLQ behavior
- Adding job metadata

---

### channels.py - Message Routing
**What it does**: Routes messages to appropriate channels (WhatsApp, Email, etc.)

**Architecture**:
```python
class ChannelRouter:
    def send(to_number, message_text, channel, template_id=None):
        # Routes to appropriate adapter
        
class WhatsAppCloudAdapter:
    # Official Meta API (15s delay, 24h window, templates)
    
class WhatsAppWebAdapter:
    # Browser automation (60s+ jitter, free-text, no cost)
    
class EmailAdapter:
    # SMTP sending (quiet hours, suppression list)
```

**Channel selection**:
```python
# In worker.py ai_engage task:
lead_contact = db.query(LeadContact).filter_by(lead_id=lead.id).first()
preferred_channel = lead_contact.preferred_channel if lead_contact else "whatsapp_cloud"

channel_router.send(
    to_number=phone_number,
    message_text=ai_response,
    channel=preferred_channel
)
```

**When to modify**:
- Adding new channels (SMS, Telegram, etc.)
- Changing rate limits or policies
- Implementing actual API integrations (marked with TODO)
- Modifying message formatting

**Integration TODOs**:
- WhatsApp Cloud: Replace placeholder with Meta Graph API
- WhatsApp Web: Implement Playwright automation
- Email: Configure actual SMTP sending

---

### celery_app.py - Task Queue Config
**What it does**: Configures Celery for distributed task processing

**Configuration**:
```python
CELERY_BROKER_URL = "redis://localhost:6379/0"  # Message broker
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"  # Result storage

# Priority support
task_acks_late = True
worker_prefetch_multiplier = 1
```

**When to modify**:
- Changing Redis connection
- Adding task routing rules
- Configuring serialization
- Setting timeouts

---

### ai.py - OpenAI Integration
**What it does**: Handles OpenAI API calls for chat completions

**Key function**:
```python
def get_ai_response(message_text, system_prompt="", conversation_history=None, temperature=0.7):
    # Calls OpenAI ChatCompletion API
    # Returns AI-generated response
```

**When to modify**:
- Changing AI model (GPT-4, Claude, etc.)
- Modifying prompt engineering
- Adding context or memory
- Implementing RAG (pgvector search)

---

### rules.py - Business Logic
**What it does**: Centralized business rules and validation logic

**When to modify**:
- Adding lead qualification logic
- Implementing BANT scoring
- Adding stage transition rules
- Custom validation logic

---

### schemas.py - API Models
**What it does**: Pydantic models for request/response validation

**Example**:
```python
class InboundMessageRequest(BaseModel):
    phone_number: str
    contact_name: str
    message_text: str
    channel: str = "whatsapp_cloud"
    company_id: Optional[str] = None
```

**When to modify**:
- Adding new API endpoints
- Changing request/response formats
- Adding validation rules

---

## 🚀 Startup Scripts

### start.ps1
**Purpose**: Start FastAPI API server

**What it does**:
1. Validates `.venv` exists
2. Loads `.env` variables
3. Starts Uvicorn on port 8000 with hot reload

**When to modify**:
- Changing port or host
- Adding environment checks
- Modifying Uvicorn settings

---

### start-worker.ps1
**Purpose**: Start Celery background worker

**What it does**:
1. Validates `.venv` exists
2. Checks Redis connection (port 6379)
3. Loads `.env` variables
4. Starts Celery with 4 concurrent workers

**When to modify**:
- Changing concurrency level
- Adding pre-flight checks
- Modifying worker pool type

---

### start-all.ps1
**Purpose**: Start all services including Docker

**What it does**:
1. Checks Docker availability
2. Starts PostgreSQL + Redis containers
3. Shows service status
4. Displays next steps

**When to modify**:
- Adding new Docker services
- Changing startup order
- Adding health checks

---

## 🔄 Data Flow

### Inbound Message Flow
```
1. External System (WhatsApp, Email)
   ↓
2. POST /inbound-message (main.py)
   ↓
3. Auto-create Company/Pipeline/Stages if needed
   ↓
4. Create/update Lead record
   ↓
5. Save Message to database
   ↓
6. Log Event (audit trail)
   ↓
7. enqueue_job("ai.engage") with priority 100
   ↓
8. Celery picks up job (worker.py)
   ↓
9. ai_engage task executes:
   - Fetch lead & message
   - Get AI configuration
   - Search knowledge base (TODO)
   - Call OpenAI API
   - Route through channel adapter
   - Log outbound message
   - Create event
   ↓
10. Job marked as completed
```

### Queue Job Lifecycle
```
enqueue_job()
   ↓
Job record created (status: queued)
   ↓
Celery task triggered
   ↓
mark_job_started() → status: processing
   ↓
Task executes
   ↓
Success? → mark_job_completed() → status: completed
   ↓
Failure? → mark_job_failed()
   ↓
Retry attempt < 5? → Re-enqueue with delay
   ↓
Retry exhausted? → status: dlq (Dead Letter Queue)
```

---

## 🛠️ Common Development Tasks

### Adding a New API Endpoint

**1. Define schema** (schemas.py):
```python
class NewFeatureRequest(BaseModel):
    param1: str
    param2: int
```

**2. Add endpoint** (main.py):
```python
@app.post("/new-feature")
def new_feature(request: NewFeatureRequest):
    # Your logic here
    return {"status": "ok"}
```

**3. Test**:
```bash
.\start.ps1
# Visit http://127.0.0.1:8000/docs
```

---

### Adding a New Background Task

**1. Define priority** (queue_manager.py):
```python
PRIORITIES = {
    "my.new.task": 85,  # Add your task
    # ... existing tasks
}
```

**2. Create task** (worker.py):
```python
@celery_app.task(priority=85)
def my_new_task(param1, param2):
    db = SessionLocal()
    try:
        # Your logic here
        mark_job_completed(job_id, result="success")
    except Exception as e:
        mark_job_failed(job_id, str(e))
    finally:
        db.close()
```

**3. Enqueue from anywhere**:
```python
from queue_manager import enqueue_job

job = enqueue_job(
    task_name="my.new.task",
    task_params={"param1": "value", "param2": 123}
)
```

---

### Adding a New Database Table

**1. Define model** (models.py):
```python
class MyNewTable(Base):
    __tablename__ = "my_new_table"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"))
    name = Column(String, nullable=False)
    attributes = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="my_new_tables")
```

**2. Add relationship** (in Company model):
```python
class Company(Base):
    # ... existing fields
    my_new_tables = relationship("MyNewTable", back_populates="company")
```

**3. Restart server** (tables auto-create):
```bash
.\start.ps1
```

---

### Adding a New Channel Adapter

**1. Create adapter class** (channels.py):
```python
class MyNewChannelAdapter:
    def send(self, to_number: str, message_text: str, template_id: str = None):
        # Implement your channel logic
        print(f"Sending via MyChannel to {to_number}: {message_text}")
        # TODO: Integrate actual API
```

**2. Register in router** (channels.py):
```python
class ChannelRouter:
    def send(self, to_number, message_text, channel, template_id=None):
        if channel == "mynewchannel":
            adapter = MyNewChannelAdapter()
            adapter.send(to_number, message_text, template_id)
        # ... existing channels
```

**3. Use in worker** (worker.py):
```python
channel_router.send(
    to_number=phone_number,
    message_text=ai_response,
    channel="mynewchannel"
)
```

---

### Modifying AI Behavior

**1. Update system prompt** (worker.py ai_engage task):
```python
system_prompt = ai_model.system_prompt if ai_model else """
You are a helpful sales assistant. Your custom instructions here...
"""
```

**2. Adjust temperature** (ai.py):
```python
def get_ai_response(..., temperature=0.7):  # 0.0 = deterministic, 1.0 = creative
```

**3. Add knowledge base search** (TODO in worker.py):
```python
# Search KB docs using pgvector similarity
kb_context = search_kb_docs(lead.company_id, message_text)
system_prompt += f"\n\nRelevant context:\n{kb_context}"
```

---

## 🧪 Testing

### Manual API Testing

**Test inbound message**:
```bash
curl -X POST http://127.0.0.1:8000/inbound-message \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "contact_name": "Test User",
    "message_text": "Hello, I need help",
    "channel": "whatsapp_cloud"
  }'
```

**Check queue stats**:
```bash
curl http://127.0.0.1:8000/queue/stats
```

---

### Database Inspection

**SQLite**:
```bash
.venv/Scripts/python.exe

>>> from database import SessionLocal
>>> from models import Lead, Message, Job
>>> db = SessionLocal()
>>> 
>>> # Check leads
>>> leads = db.query(Lead).all()
>>> print(f"Total leads: {len(leads)}")
>>> 
>>> # Check recent jobs
>>> jobs = db.query(Job).order_by(Job.created_at.desc()).limit(10).all()
>>> for job in jobs:
...     print(f"{job.task_name} - {job.status}")
```

**PostgreSQL**:
```bash
docker exec -it ai-auto-postgres psql -U myuser -d ai_auto_db

SELECT * FROM leads LIMIT 5;
SELECT * FROM jobs WHERE status = 'processing';
SELECT * FROM messages ORDER BY created_at DESC LIMIT 10;
```

---

## 📊 Monitoring & Debugging

### Check Service Health

```powershell
# API server
curl http://127.0.0.1:8000/docs

# Redis
docker ps | grep redis

# PostgreSQL
docker ps | grep postgres

# Queue stats
curl http://127.0.0.1:8000/queue/stats
```

### View Logs

- **API logs**: Terminal 1 (where start.ps1 is running)
- **Worker logs**: Terminal 2 (where start-worker.ps1 is running)
- **Docker logs**: `docker logs ai-auto-postgres` or `docker logs ai-auto-redis`

### Common Debugging Steps

1. **Job not processing?**
   - Check worker terminal for errors
   - Verify Redis connection: `docker ps | grep redis`
   - Check `/queue/stats` for stuck jobs

2. **AI not responding?**
   - Verify `OPENAI_API_KEY` in .env
   - Check worker logs for API errors
   - Review job status in database: `SELECT * FROM jobs WHERE status = 'failed'`

3. **Database connection error?**
   - For SQLite: Check if `test.db` exists and is writable
   - For PostgreSQL: Verify Docker container is running

---

## 🎯 Architecture Principles

### Event Sourcing
Every action creates an `Event` record:
```python
event = Event(
    id=str(uuid.uuid4()),
    type="message.inbound",
    entity_type="lead",
    entity_id=lead.id,
    payload={"message_id": message.id, "text": message.text}
)
```

### Queue-First Design
Everything that can be async, should be async:
- ✅ AI responses → queued
- ✅ Follow-ups → queued
- ✅ Sequences → queued
- ✅ Webhooks → queued
- ❌ API requests → immediate (but fast, just enqueue jobs)

### Idempotency
All jobs use idempotency keys to prevent duplicates:
```python
job = enqueue_job(
    task_name="ai.engage",
    task_params=params,
    idempotency_key=f"ai_engage_{lead_id}_{message_id}"
)
```

### Multi-tenancy
All data isolated by `company_id`:
```python
class Lead(Base):
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
```

---

## 📝 Next Steps (TODOs)

**High Priority**:
- [ ] Integrate Meta Graph API for WhatsApp Cloud (channels.py)
- [ ] Implement Playwright automation for WhatsApp Web (channels.py)
- [ ] Configure actual SMTP sending (channels.py)
- [ ] Add pgvector for KB similarity search (worker.py, ai.py)

**Medium Priority**:
- [ ] Implement sequence execution (worker.py sequence_step)
- [ ] Implement email campaigns (worker.py email_sequence)
- [ ] Implement webhook notifications (worker.py webhook_reminder)
- [ ] Add authentication/API keys (main.py)

**Future Enhancements**:
- [ ] Phase 4-17 from SHVYA guide
- [ ] Team inbox UI
- [ ] Analytics dashboard
- [ ] CRM integrations (Salesforce, HubSpot)
- [ ] Compliance features (GDPR, TCPA)

---

## 🤝 Contributing

When making changes:

1. **Understand the flow**: Read relevant sections above
2. **Check dependencies**: See which files import your target file
3. **Test locally**: Use startup scripts to verify changes
4. **Check logs**: Monitor both API and worker terminals
5. **Update docs**: Add notes about your changes to this guide

---

## 📚 Additional Resources

- **CHANGELOG.md** - Detailed implementation history
- **QUICKSTART.md** - Quick setup guide
- **USAGE.md** - Complete usage documentation
- **README.md** - Project overview

---

