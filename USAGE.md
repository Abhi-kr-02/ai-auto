# SHVYA AI Auto - Usage Guide

Complete guide for using and operating the SHVYA AI automation platform.

---

## Table of Contents

1. [Startup Scripts](#startup-scripts)
2. [API Endpoints](#api-endpoints)
3. [Queue System](#queue-system)
4. [Channel Adapters](#channel-adapters)
5. [Worker Tasks](#worker-tasks)
6. [Database Management](#database-management)
7. [Configuration](#configuration)
8. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## Startup Scripts

### start.ps1 - Start API Server

**Purpose**: Launches the FastAPI web server with hot reload for development.

**Usage**:
```powershell
.\start.ps1
```

**What it does**:
1. Validates that `.venv` virtual environment exists
2. Loads environment variables from `.env` file (if present)
3. Starts Uvicorn server on `http://127.0.0.1:8000`
4. Enables auto-reload on code changes

**When to use**:
- Starting the REST API server
- Development with hot reload
- Testing API endpoints via Swagger UI at `/docs`

**Requirements**:
- Python virtual environment in `.venv/`
- Optional: `.env` file for configuration

---

### start-worker.ps1 - Start Celery Worker

**Purpose**: Launches the Celery worker to process background jobs from the queue.

**Usage**:
```powershell
.\start-worker.ps1
```

**What it does**:
1. Validates virtual environment exists
2. Checks Redis connection on port 6379
3. Loads environment variables from `.env`
4. Starts Celery worker with 4 concurrent threads
5. Enables priority-based task routing

**When to use**:
- Processing AI engagement tasks
- Handling follow-up messages
- Running scheduled sequences
- Any background job processing

**Requirements**:
- Redis running on `localhost:6379` (or via Docker)
- Virtual environment in `.venv/`
- `.env` file with configuration

**Worker Configuration**:
- Pool: `solo` (single process, Windows compatible)
- Concurrency: 4 threads
- Queue: `celery` with priority support

---

### start-all.ps1 - Start All Services

**Purpose**: One-command startup for entire stack including Docker services.

**Usage**:
```powershell
.\start-all.ps1
```

**What it does**:
1. Checks if Docker is available
2. Starts PostgreSQL + Redis containers via `docker-compose.yml`
3. Displays service status
4. Shows commands to start API server and worker

**When to use**:
- First time setup
- Starting fresh development session
- Running full stack with PostgreSQL

**Services Started**:
- PostgreSQL (port 5432)
- Redis (port 6379)

**Next Steps After Running**:
```powershell
# Terminal 1 - Start API
.\start.ps1

# Terminal 2 - Start Worker
.\start-worker.ps1
```

---

## API Endpoints

### POST /inbound-message

**Purpose**: Receive incoming messages from any channel (WhatsApp, Email, etc.)

**Usage**:
```bash
POST http://127.0.0.1:8000/inbound-message
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "contact_name": "John Doe",
  "message_text": "I'm interested in your product",
  "channel": "whatsapp_cloud",
  "company_id": "optional-uuid"
}
```

**Behavior**:
1. **Auto-creates missing entities**:
   - If `company_id` not provided → creates new Company
   - If Pipeline doesn't exist → creates default Pipeline
   - If Stages don't exist → creates 5 default stages (New, Contacted, Qualified, Proposal, Closed)

2. **Creates/updates Lead**:
   - Searches for existing lead by phone number
   - Creates new lead if not found
   - Updates contact info if found

3. **Logs Message**:
   - Stores in `messages` table
   - Tracks channel and timestamp
   - Links to lead

4. **Logs Event**:
   - Creates audit trail in `events` table
   - Records message receipt

5. **Enqueues AI Job**:
   - Priority: 100 (P1 - highest)
   - Task: `ai_engage`
   - Idempotency: Prevents duplicate jobs

**Response**:
```json
{
  "status": "ok",
  "message_id": "uuid",
  "job_id": "uuid"
}
```

**Use Cases**:
- Webhook receiver for WhatsApp Cloud API
- Integration endpoint for chat platforms
- Email-to-API gateway
- Manual message injection for testing

---

### GET /queue/stats

**Purpose**: Monitor queue health and job processing metrics

**Usage**:
```bash
GET http://127.0.0.1:8000/queue/stats
```

**Response**:
```json
{
  "queued": 5,
  "processing": 2,
  "completed": 143,
  "failed": 3,
  "dlq": 1,
  "total": 154
}
```

**Metrics Explained**:
- `queued`: Jobs waiting to be processed
- `processing`: Jobs currently being executed
- `completed`: Successfully finished jobs
- `failed`: Jobs that failed but can retry
- `dlq`: Dead Letter Queue - jobs that exhausted retries
- `total`: All jobs ever created

**Use Cases**:
- Dashboard monitoring
- Health checks
- Performance analysis
- Detecting stuck workers

---

### POST /admin/dlq/replay

**Purpose**: Replay failed jobs from Dead Letter Queue

**Usage**:
```bash
POST http://127.0.0.1:8000/admin/dlq/replay
Content-Type: application/json

{
  "max_jobs": 10
}
```

**Behavior**:
1. Fetches up to `max_jobs` from DLQ
2. Resets each job status to `queued`
3. Resets attempt counter to 0
4. Re-enqueues jobs with original priority

**Response**:
```json
{
  "replayed": 3,
  "job_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Use Cases**:
- Recovering from temporary failures (API downtime, network issues)
- Replaying jobs after bug fixes
- Manual intervention for critical jobs

**Safety**:
- Only replays jobs with `status = 'dlq'`
- Maintains original task parameters
- Idempotency keys prevent duplicates

---

## Queue System

### Priority Levels

**P1 - Conversational (90-100)**:
- `ai.engage` (100): Immediate AI response to inbound messages
- `followup.bumpup` (95): Smart follow-up messages
- `ai.summary` (90): Conversation summarization

**P2 - Scheduled (50-70)**:
- `sequence.step` (70): Automated sequence steps
- `email.sequence` (60): Email campaign sends
- `webhook.reminder` (50): Webhook notifications

**Priority Selection Logic**:
```python
# High priority = quick turnaround, user is waiting
# Low priority = scheduled, can be delayed
```

---

### Enqueuing Jobs

**Via API** (Automatic):
```python
# Handled automatically by POST /inbound-message
```

**Programmatic** (Advanced):
```python
from queue_manager import enqueue_job

job = enqueue_job(
    task_name="ai.engage",
    task_params={"lead_id": "uuid", "message_id": "uuid"},
    idempotency_key="unique-key",  # Optional
    priority=100  # Optional, defaults to task priority
)
```

**Idempotency**:
- Prevents duplicate job execution
- Uses unique `idempotency_key`
- Returns existing job if key matches

---

### Job Lifecycle

```
queued → processing → completed
           ↓
        failed (retry)
           ↓
        failed (retry)
           ↓
        failed (retry)
           ↓
          dlq (dead letter queue)
```

**Retry Schedule**:
1. 5 seconds
2. 20 seconds
3. 60 seconds (1 minute)
4. 180 seconds (3 minutes)
5. 600 seconds (10 minutes)
6. → DLQ (Dead Letter Queue)

---

### Queue Monitoring

**Check Queue Stats**:
```bash
curl http://127.0.0.1:8000/queue/stats
```

**Check Database Directly**:
```sql
-- Active jobs
SELECT * FROM jobs WHERE status = 'processing';

-- Failed jobs
SELECT * FROM jobs WHERE status = 'failed' ORDER BY updated_at DESC;

-- DLQ jobs
SELECT * FROM jobs WHERE status = 'dlq';
```

**Worker Logs**:
- Monitor Terminal 2 (worker terminal) for real-time execution logs
- Each task logs start, progress, and completion

---

## Channel Adapters

### WhatsApp Cloud API Adapter

**Purpose**: Send messages via Meta's WhatsApp Cloud API (official)

**Configuration**:
```python
WHATSAPP_CLOUD_PHONE_ID = "your-phone-id"
WHATSAPP_CLOUD_TOKEN = "your-access-token"
```

**Usage** (Automatic):
```python
from channels import channel_router

channel_router.send(
    to_number="+1234567890",
    message_text="Hello from SHVYA!",
    channel="whatsapp_cloud",
    template_id="optional-template-uuid"
)
```

**Policies**:
- **Rate Limiting**: 15-second delay between messages
- **24-Hour Window**: Can only send templates outside 24h window
- **Template Requirement**: First message must use approved template
- **Free-Text**: Allowed within 24h session

**Integration Status**: `TODO` - Requires Meta Graph API setup

**Implementation**:
```python
# TODO: Replace placeholder with actual API call
requests.post(
    f"https://graph.facebook.com/v18.0/{phone_id}/messages",
    headers={"Authorization": f"Bearer {token}"},
    json=payload
)
```

---

### WhatsApp Web Adapter

**Purpose**: Send messages via WhatsApp Web automation (unofficial)

**Configuration**:
```python
# No API keys required - uses browser automation
```

**Usage** (Automatic):
```python
channel_router.send(
    to_number="+1234567890",
    message_text="Hello from SHVYA!",
    channel="whatsapp_web"
)
```

**Policies**:
- **Rate Limiting**: 60+ seconds with random jitter (anti-detection)
- **Human-Like**: Randomized delays to mimic human behavior
- **Free-Text**: No template restrictions
- **No Cost**: Free to use (vs Cloud API charges)

**Integration Status**: `TODO` - Requires Playwright automation

**Implementation**:
```python
# TODO: Replace placeholder with Playwright automation
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    # ... WhatsApp Web automation logic
```

---

### Email Adapter

**Purpose**: Send emails via SMTP (Gmail, SendGrid, AWS SES, etc.)

**Configuration**:
```python
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
```

**Usage** (Automatic):
```python
channel_router.send(
    to_number="contact@example.com",  # Email address
    message_text="Email body content",
    channel="email",
    template_id="optional-template-uuid"
)
```

**Policies**:
- **Quiet Hours**: Only sends between 8 AM - 10 PM (local time)
- **Suppression List**: Checks against unsubscribe list
- **Delay**: No artificial delay (email is async by nature)

**Integration Status**: `TODO` - Requires actual SMTP configuration

**Implementation**:
```python
# TODO: Replace placeholder with actual SMTP sending
import smtplib
from email.mime.text import MIMEText

msg = MIMEText(message_text)
msg["Subject"] = "Subject here"
msg["From"] = SMTP_USER
msg["To"] = to_email

with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.send_message(msg)
```

---

## Worker Tasks

### ai_engage (Priority 100)

**Purpose**: Generate AI-powered response to inbound message

**Triggered By**: POST /inbound-message endpoint

**Process**:
1. Fetch lead and message from database
2. Load AI configuration for lead's company
3. Search knowledge base for relevant context (TODO: implement pgvector)
4. Build conversation history
5. Call OpenAI API for response
6. Route response through appropriate channel adapter
7. Log outbound message
8. Create event audit trail
9. Mark job as completed

**Configuration**:
```python
# In models.AIModel table
temperature = 0.7  # Creativity level
max_tokens = 500   # Response length
system_prompt = "You are a helpful sales assistant..."
```

**Retry Logic**: 
- 5 retries with exponential backoff
- Handles OpenAI API errors gracefully

---

### followup_bumpup (Priority 95)

**Purpose**: Send smart follow-up to re-engage cold leads

**Triggered By**: Manual or scheduled job

**Process**:
1. Fetch lead information
2. Analyze conversation context
3. Generate personalized bump-up message with variation
4. Send via WhatsApp only (high engagement channel)
5. Update lead attributes with bump-up timestamp

**Message Variations**:
- "Hey! Just following up..."
- "Hi! Wanted to check in..."
- "Hello! Circling back..."

**Use Cases**:
- Re-engaging leads after 3 days of silence
- Moving leads stuck in pipeline stages
- Warming up cold prospects

---

### ai_summary (Priority 90)

**Purpose**: Summarize conversation for quick context

**Triggered By**: Manual request or post-conversation

**Process**:
1. Fetch all messages for lead
2. Build conversation thread
3. Call OpenAI API for summarization
4. Store summary in `lead.attributes['summary']`

**Output Format**:
```json
{
  "summary": "Customer interested in Enterprise plan. Budget concerns. Follow-up in 2 weeks.",
  "key_points": ["Enterprise interest", "Budget $5k/mo", "Decision maker: CTO"],
  "sentiment": "positive",
  "next_action": "Send pricing proposal"
}
```

**Use Cases**:
- Team handoffs
- Manager review
- Pipeline reporting
- CRM sync

---

### sequence_step (Priority 70)

**Purpose**: Execute next step in automated sequence

**Triggered By**: Scheduled by sequence automation

**Process** (TODO):
1. Fetch sequence and current step
2. Check if conditions met
3. Execute step action (send message, wait, end)
4. Update lead position in sequence
5. Schedule next step if applicable

**Use Cases**:
- Drip campaigns
- Onboarding sequences
- Educational content series
- Re-engagement campaigns

---

### email_sequence (Priority 60)

**Purpose**: Send scheduled email in campaign

**Triggered By**: Email campaign scheduler

**Process** (TODO):
1. Fetch email template
2. Personalize with lead data
3. Check quiet hours and suppression list
4. Send via Email adapter
5. Track open/click metrics

**Use Cases**:
- Newsletter campaigns
- Product announcements
- Event invitations
- Re-engagement emails

---

### webhook_reminder (Priority 50)

**Purpose**: Send webhook notification for external integrations

**Triggered By**: Event triggers or schedules

**Process** (TODO):
1. Fetch webhook configuration
2. Build payload with event data
3. Sign payload (HMAC)
4. POST to webhook URL with retry
5. Log delivery status

**Use Cases**:
- CRM synchronization
- Slack notifications
- Zapier integrations
- Custom dashboards

---

## Database Management

### Viewing Data

**SQLite** (Development):
```bash
# Using DB Browser for SQLite (GUI)
# Or via Python:
.venv/Scripts/python.exe

>>> from database import SessionLocal
>>> from models import Lead, Message
>>> db = SessionLocal()
>>> leads = db.query(Lead).all()
>>> for lead in leads:
...     print(lead.phone_number, lead.contact_name)
```

**PostgreSQL** (Production):
```bash
# Connect via Docker
docker exec -it ai-auto-postgres psql -U myuser -d ai_auto_db

# Common queries
SELECT * FROM leads LIMIT 10;
SELECT * FROM jobs WHERE status = 'processing';
SELECT * FROM messages ORDER BY created_at DESC LIMIT 20;
```

---

### Database Schema

**16 Tables**:
1. `companies` - Multi-tenant organizations
2. `users` - Team members and access control
3. `pipelines` - Sales pipeline definitions
4. `stages` - Pipeline stages (New, Qualified, etc.)
5. `leads` - Contact records with attributes
6. `lead_contacts` - Multi-channel contact info
7. `messages` - Conversation history
8. `events` - Audit trail and event sourcing
9. `sequences` - Automation workflows
10. `sequence_steps` - Individual sequence actions
11. `templates` - Message templates
12. `ai_models` - AI configuration per company
13. `ai_kb_docs` - Knowledge base documents
14. `ai_sessions` - Conversation context tracking
15. `jobs` - Queue job records
16. `report_caches` - Pre-computed analytics

**Key Relationships**:
- Company → Users, Pipelines, AIModels, Leads
- Pipeline → Stages
- Lead → Messages, LeadContacts, Events
- Sequence → SequenceSteps

---

### Migrations

**Current**: Auto-creation on startup via `Base.metadata.create_all()`

**Future** (Recommended): Use Alembic for version control
```bash
# Initialize Alembic
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head
```

---

## Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/ai_auto_db
# Or for SQLite (development):
# DATABASE_URL=sqlite:///./test.db

# Redis (Celery broker)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# OpenAI API
OPENAI_API_KEY=sk-proj-...

# WhatsApp Cloud API (optional)
WHATSAPP_CLOUD_PHONE_ID=your-phone-id
WHATSAPP_CLOUD_TOKEN=your-access-token

# Email SMTP (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

### Loading Configuration

**Option 1**: `.env` file (Recommended)
```bash
# Create .env in project root
cp env.example .env
# Edit .env with your values
```

**Option 2**: System environment variables
```powershell
$env:OPENAI_API_KEY = "sk-proj-..."
$env:DATABASE_URL = "postgresql://..."
```

**Option 3**: Docker environment
```yaml
# docker-compose.yml
environment:
  - OPENAI_API_KEY=sk-proj-...
```

---

## Monitoring & Troubleshooting

### Health Checks

**API Server**:
```bash
curl http://127.0.0.1:8000/docs
# Should load Swagger UI
```

**Celery Worker**:
```powershell
# Check worker terminal for:
[INFO/MainProcess] celery@hostname ready.
```

**Redis**:
```bash
docker ps | grep redis
# Or:
redis-cli ping  # Should return PONG
```

**Database**:
```bash
# PostgreSQL
docker ps | grep postgres

# SQLite
ls test.db  # Should exist
```

---

### Common Issues

**Issue**: "Redis connection refused"
```
Solution: Start Redis container
docker compose up -d redis
```

**Issue**: "uvicorn: command not found"
```
Solution: Activate virtual environment
.venv\Scripts\Activate.ps1
```

**Issue**: "No module named 'celery'"
```
Solution: Install dependencies
.venv\Scripts\pip.exe install -r requirements.txt
```

**Issue**: "Port 8000 already in use"
```
Solution: Kill existing process
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

**Issue**: "Worker not processing jobs"
```
Solution 1: Check Redis connection
Solution 2: Verify queue stats (/queue/stats)
Solution 3: Restart worker with .\start-worker.ps1
```

---

### Logging

**API Logs**: Terminal 1 (Uvicorn output)
```
INFO: 127.0.0.1:52890 - "POST /inbound-message HTTP/1.1" 200 OK
```

**Worker Logs**: Terminal 2 (Celery output)
```
[INFO/MainProcess] Task ai_engage[uuid] received
[INFO/ForkPoolWorker-1] Task ai_engage[uuid] succeeded in 2.5s
```

**Database Logs**: `events` table
```sql
SELECT * FROM events ORDER BY created_at DESC LIMIT 50;
```

---

### Performance Tuning

**Worker Concurrency**:
```powershell
# Edit start-worker.ps1
--concurrency=8  # Increase from 4 to 8
```

**Database Connection Pool**:
```python
# In database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Increase from default 5
    max_overflow=40
)
```

**Celery Task Timeout**:
```python
# In worker.py
@celery_app.task(time_limit=60)  # 60 second max
def ai_engage(lead_id, message_id):
    # ...
```

---

## Quick Reference

### Daily Operations

```powershell
# Start stack
.\start-all.ps1        # Start Docker services
.\start.ps1            # Terminal 1 - API
.\start-worker.ps1     # Terminal 2 - Worker

# Monitor
http://127.0.0.1:8000/docs         # API docs
http://127.0.0.1:8000/queue/stats  # Queue health

# Troubleshoot
docker logs ai-auto-postgres       # DB logs
docker logs ai-auto-redis          # Redis logs
```

### Testing Workflow

```bash
# 1. Send test message
curl -X POST http://127.0.0.1:8000/inbound-message \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "contact_name": "Test User", "message_text": "Hello", "channel": "whatsapp_cloud"}'

# 2. Check queue stats
curl http://127.0.0.1:8000/queue/stats

# 3. Monitor worker logs in Terminal 2

# 4. Check database
sqlite3 test.db "SELECT * FROM messages ORDER BY created_at DESC LIMIT 5;"
```

---

**For more details, see**:
- [CHANGELOG.md](CHANGELOG.md) - Implementation details
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [README.md](README.md) - Project overview
