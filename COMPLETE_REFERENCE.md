# SHVYA AI Auto - Complete Reference Guide

Complete documentation covering all commands, workflows, libraries, tools, and architecture.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack - All Libraries & Tools](#tech-stack)
3. [Architecture & Workflow](#architecture--workflow)
4. [Installation & Setup Commands](#installation--setup-commands)
5. [Running the System](#running-the-system)
6. [API Commands & Endpoints](#api-commands--endpoints)
7. [Database Commands](#database-commands)
8. [Docker Commands](#docker-commands)
9. [Testing Commands](#testing-commands)
10. [Complete Workflows](#complete-workflows)
11. [File Structure](#file-structure)
12. [Configuration Guide](#configuration-guide)

---

## 📖 Project Overview

**SHVYA AI Auto** is a complete AI-powered sales automation platform designed for course selling and lead engagement through multiple channels (WhatsApp Web, WhatsApp Cloud API, Email).

**Use Case:** 
- Student fills form on website
- AI automatically responds via WhatsApp/Email
- Bot engages like a human to sell courses
- Auto follow-ups until conversion
- Complete lead tracking in CRM

**Key Features:**
- 🤖 AI-powered conversations (OpenAI GPT-4)
- 💬 WhatsApp Web automation (Playwright)
- 📧 Multi-channel support (WhatsApp + Email)
- 🎯 Priority-based job queue
- 📊 Full CRM with 16-table database
- 🔄 Auto follow-ups and sequences
- 📝 Event sourcing & audit trails

---

## 🛠️ Tech Stack - All Libraries & Tools

### **Core Framework**
| Library | Version | Purpose |
|---------|---------|---------|
| **FastAPI** | 0.104.1+ | REST API web framework |
| **Uvicorn** | 0.24.0+ | ASGI server for FastAPI |
| **Pydantic** | 2.5.0+ | Data validation & schemas |

### **Database & ORM**
| Library | Version | Purpose |
|---------|---------|---------|
| **SQLAlchemy** | 2.0.23+ | ORM for database operations |
| **psycopg2-binary** | 2.9.11+ | PostgreSQL adapter |
| **PostgreSQL** | 15 | Production database (Docker) |
| **SQLite** | Built-in | Development fallback |

### **Task Queue & Background Jobs**
| Library | Version | Purpose |
|---------|---------|---------|
| **Celery** | 5.3.4+ | Distributed task queue |
| **Redis** | 7 Alpine | Message broker for Celery |
| **redis (Python)** | 5.0.1+ | Redis client library |

### **AI & Intelligence**
| Library | Version | Purpose |
|---------|---------|---------|
| **OpenAI** | 1.3.5+ | GPT-4o-mini for AI responses |

### **Browser Automation**
| Library | Version | Purpose |
|---------|---------|---------|
| **Playwright** | 1.57.0+ | WhatsApp Web automation |
| **Chromium** | 143.0.7499.4 | Browser for Playwright |

### **HTTP & Communication**
| Library | Version | Purpose |
|---------|---------|---------|
| **requests** | 2.31.0+ | HTTP client for APIs |
| **smtplib** | Built-in | Email sending (SMTP) |

### **Utilities**
| Library | Version | Purpose |
|---------|---------|---------|
| **python-dotenv** | 1.0.0+ | Environment variable management |

### **Infrastructure**
| Tool | Version | Purpose |
|------|---------|---------|
| **Docker** | 29.1.3+ | Containerization |
| **Docker Compose** | Latest | Multi-container orchestration |
| **PowerShell** | 5.1+ | Windows automation scripts |
| **Python** | 3.12+ | Runtime environment |

---

## 🏗️ Architecture & Workflow

### **System Architecture**

```
┌─────────────────────────────────────────────────────┐
│                  External World                      │
│  (Website Forms, WhatsApp, Email, Webhooks)         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Server (Port 8000)             │
│  • POST /inbound-message (webhook)                  │
│  • GET /queue/stats (monitoring)                    │
│  • POST /admin/dlq/replay (admin)                   │
│  • Auto-creates Company/Pipeline/Stages             │
│  • Creates/updates Leads                            │
│  • Enqueues jobs with idempotency                   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│         PostgreSQL Database (Port 5432)             │
│  16 Tables:                                         │
│  • companies, users, pipelines, stages              │
│  • leads, lead_contacts, messages                   │
│  • events, jobs, sequences, sequence_steps          │
│  • templates, ai_models, ai_kb_docs                 │
│  • ai_sessions, reports_cache                       │
└─────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│            Redis Queue (Port 6379)                  │
│  Priority-based job queue:                          │
│  • P1 (90-100): AI responses, follow-ups            │
│  • P2 (50-70): Sequences, emails, webhooks          │
│  • DLQ: Failed jobs with retry logic                │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              Celery Worker                          │
│  6 Background Tasks:                                │
│  1. ai_engage (100) - AI responses                  │
│  2. followup_bumpup (95) - Smart follow-ups         │
│  3. ai_summary (90) - Conversation summaries        │
│  4. sequence_step (70) - Automation sequences       │
│  5. email_sequence (60) - Email campaigns           │
│  6. webhook_reminder (50) - Webhook notifications   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│            AI Service (OpenAI)                      │
│  • GPT-4o-mini model                                │
│  • Temperature: 0.7                                 │
│  • Max tokens: 500                                  │
│  • System prompts from database                     │
│  • Knowledge base search                            │
└─────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          Channel Routing System                     │
│  Multi-channel adapters:                            │
│  • WhatsApp Web (Playwright) ✅                     │
│  • WhatsApp Cloud API (Meta) 🔧                     │
│  • Email (SMTP/SES) 🔧                              │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│            WhatsApp Web Browser                     │
│  • Chromium via Playwright                          │
│  • Session persistence (./whatsapp_session/)        │
│  • Human-like typing (50-150ms per char)            │
│  • Smart delays (60s ± 15s)                         │
│  • Auto-login (QR scan once)                        │
└─────────────────────────────────────────────────────┘
```

### **Data Flow - Complete Workflow**

```
1. INBOUND MESSAGE
   Student fills form on website
   Form submits to: POST /inbound-message
   {
     "phone_number": "+919876543210",
     "contact_name": "Rahul Kumar",
     "message_text": "Interested in Digital Marketing course",
     "channel": "whatsapp_web",
     "company_id": "optional"
   }
   
2. API PROCESSING (main.py)
   ✓ Auto-create Company (if missing)
   ✓ Auto-create Pipeline with 5 stages
   ✓ Create/Update Lead record
   ✓ Save Message to database
   ✓ Log Event for audit trail
   ✓ Generate idempotency key
   
3. JOB ENQUEUEING (queue_manager.py)
   ✓ Create Job record (status: queued)
   ✓ Set priority: 100 (P1 - highest)
   ✓ Enqueue to Celery with task_name: "ai.engage"
   ✓ Return job_id to API
   
4. CELERY WORKER PICKS UP JOB (worker.py)
   ✓ Update job status: processing
   ✓ Execute ai_engage(lead_id, message_id)
   
5. AI PROCESSING (ai.py)
   ✓ Fetch lead and message from database
   ✓ Get AI configuration (company's AIModel)
   ✓ Search knowledge base (AIKBDoc) for course info
   ✓ Build conversation history
   ✓ Call OpenAI API with:
     - System prompt (course selling instructions)
     - Conversation history
     - Current message
   ✓ Receive AI-generated response
   
6. CHANNEL ROUTING (channels.py)
   ✓ Select channel: "whatsapp_web"
   ✓ Route to WhatsAppWebAdapter.send()
   
7. WHATSAPP WEB AUTOMATION (Playwright)
   ✓ Get/create browser session
   ✓ Check if logged in (or scan QR code)
   ✓ Navigate to: wa.me/{phone_number}
   ✓ Wait for message input box
   ✓ Type message with human-like delays:
     - 50-150ms per character
     - 100-300ms between words
     - 0.5-1.5s before sending
   ✓ Press Enter to send
   ✓ Wait 2s for confirmation
   
8. RESULT LOGGING
   ✓ Save outbound Message to database
   ✓ Log Event (message.sent)
   ✓ Update Job status: completed
   ✓ Store external_id from WhatsApp
   
9. FOLLOW-UP SCHEDULING (Optional)
   If no response in 24 hours:
   ✓ Enqueue followup_bumpup job (priority: 95)
   ✓ Send smart follow-up message
   ✓ Continue until conversion or opt-out
```

---

## 💻 Installation & Setup Commands

### **1. Initial Setup**

```powershell
# Clone or navigate to project
cd E:\ai-auto

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install all dependencies
.\.venv\Scripts\pip.exe install -r requirements.txt

# Install Playwright browsers
.\.venv\Scripts\playwright.exe install chromium
```

### **2. Docker Setup**

```powershell
# Install Docker Desktop (one-time)
winget install Docker.DockerDesktop

# Refresh PATH (after Docker install)
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verify Docker
docker --version
docker ps

# Start Docker containers
docker compose up -d

# Check container status
docker ps

# View logs
docker logs ai-auto-postgres
docker logs ai-auto-redis

# Stop containers
docker compose down

# Stop and remove volumes (full reset)
docker compose down -v
```

### **3. Environment Configuration**

```powershell
# Create .env file from template
Copy-Item .env.docker .env

# Edit .env file (add your API keys)
notepad .env
```

**.env file contents:**
```bash
# Database
DATABASE_URL=postgresql://ai:ai@localhost:5432/ai_automation

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-your-actual-api-key-here

# WhatsApp Web
WHATSAPP_SESSION_DIR=./whatsapp_session
ENV=development

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

## 🚀 Running the System

### **Option 1: Using Startup Scripts (Recommended)**

```powershell
# Terminal 1 - Start all Docker services
.\start-all.ps1

# Terminal 2 - Start API server
.\start.ps1

# Terminal 3 - Start Celery worker
.\start-worker.ps1
```

### **Option 2: Manual Commands**

```powershell
# Start Docker services
docker compose up -d

# Start API server
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Start Celery worker (new terminal)
.\.venv\Scripts\celery.exe -A worker worker --loglevel=info --pool=solo --concurrency=4
```

### **Verify Services**

```powershell
# Check Docker containers
docker ps

# Test API
Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs"

# Check queue stats
Invoke-WebRequest -Uri "http://127.0.0.1:8000/queue/stats"

# Test PostgreSQL
docker exec -it ai-auto-postgres pg_isready -U ai

# Test Redis
docker exec -it ai-auto-redis redis-cli ping
```

---

## 🌐 API Commands & Endpoints

### **Base URL**
```
http://127.0.0.1:8000
```

### **1. Inbound Message (Main Webhook)**

**Send a message to create lead and trigger AI response:**

```powershell
# PowerShell
Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:8000/inbound-message" `
  -ContentType "application/json" `
  -Body '{"phone_number":"+919876543210","contact_name":"Rahul Kumar","message_text":"Interested in Digital Marketing course","channel":"whatsapp_web"}'

# cURL (Git Bash)
curl -X POST "http://127.0.0.1:8000/inbound-message" \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+919876543210","contact_name":"Rahul Kumar","message_text":"Interested in course","channel":"whatsapp_web"}'
```

**Request Body:**
```json
{
  "phone_number": "+919876543210",
  "contact_name": "Rahul Kumar",
  "message_text": "I want to learn Digital Marketing",
  "channel": "whatsapp_web",
  "company_id": "optional-uuid"
}
```

**Response:**
```json
{
  "status": "ok",
  "message_id": "uuid-message-id",
  "job_id": "uuid-job-id"
}
```

### **2. Queue Statistics**

```powershell
# Get queue stats
Invoke-WebRequest -Uri "http://127.0.0.1:8000/queue/stats" | Select-Object Content

# Response:
# {"queued":5,"processing":2,"completed":143,"failed":3,"dlq":1}
```

### **3. Replay Failed Jobs (Admin)**

```powershell
Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:8000/admin/dlq/replay" `
  -ContentType "application/json" `
  -Body '{"max_jobs":10}'
```

### **4. API Documentation**

```powershell
# Open Swagger UI in browser
Start-Process "http://127.0.0.1:8000/docs"

# Open ReDoc
Start-Process "http://127.0.0.1:8000/redoc"
```

---

## 🗄️ Database Commands

### **PostgreSQL Commands**

```powershell
# Connect to PostgreSQL
docker exec -it ai-auto-postgres psql -U ai -d ai_automation

# Inside psql:
# List all tables
\dt

# View table structure
\d leads

# Check leads
SELECT * FROM leads ORDER BY created_at DESC LIMIT 10;

# Check messages
SELECT * FROM messages WHERE channel = 'wa_web' ORDER BY created_at DESC;

# Check jobs
SELECT task_name, status, priority, attempts FROM jobs ORDER BY created_at DESC LIMIT 20;

# Check events (audit trail)
SELECT type, entity_type, created_at FROM events ORDER BY created_at DESC LIMIT 20;

# Check AI models
SELECT * FROM ai_models;

# Exit
\q
```

### **Common Queries**

```sql
-- Count leads by stage
SELECT s.name, COUNT(l.id) 
FROM stages s 
LEFT JOIN leads l ON l.stage_id = s.id 
GROUP BY s.name;

-- Recent conversations
SELECT l.contact_name, m.text, m.direction, m.created_at 
FROM messages m 
JOIN leads l ON m.lead_id = l.id 
ORDER BY m.created_at DESC 
LIMIT 30;

-- Job statistics
SELECT status, COUNT(*) 
FROM jobs 
GROUP BY status;

-- Failed jobs
SELECT task_name, error_message, attempts, created_at 
FROM jobs 
WHERE status = 'failed' 
ORDER BY created_at DESC;
```

### **Database Backup & Restore**

```powershell
# Backup database
docker exec ai-auto-postgres pg_dump -U ai ai_automation > backup.sql

# Restore database
Get-Content backup.sql | docker exec -i ai-auto-postgres psql -U ai -d ai_automation
```

---

## 🐳 Docker Commands

### **Container Management**

```powershell
# Start all containers
docker compose up -d

# Stop all containers
docker compose down

# Restart containers
docker compose restart

# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# View container logs
docker logs ai-auto-postgres
docker logs ai-auto-redis
docker logs -f ai-auto-postgres  # Follow logs

# Access container shell
docker exec -it ai-auto-postgres bash
docker exec -it ai-auto-redis sh

# Check container resource usage
docker stats
```

### **Database Operations**

```powershell
# PostgreSQL
docker exec -it ai-auto-postgres psql -U ai -d ai_automation
docker exec ai-auto-postgres pg_isready -U ai

# Redis
docker exec -it ai-auto-redis redis-cli
docker exec ai-auto-redis redis-cli ping
docker exec ai-auto-redis redis-cli INFO
docker exec ai-auto-redis redis-cli KEYS '*'
```

### **Troubleshooting**

```powershell
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View detailed container info
docker inspect ai-auto-postgres
docker inspect ai-auto-redis

# Remove all stopped containers
docker container prune

# Remove all unused volumes
docker volume prune

# Full cleanup (WARNING: deletes all data)
docker compose down -v
docker system prune -a
```

---

## 🧪 Testing Commands

### **Test API Endpoints**

```powershell
# Health check
Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs"

# Send test message
$body = @{
    phone_number = "+919876543210"
    contact_name = "Test User"
    message_text = "Test message"
    channel = "whatsapp_web"
} | ConvertTo-Json

Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:8000/inbound-message" `
  -ContentType "application/json" -Body $body
```

### **Test WhatsApp Web**

```python
# Python console test
.\.venv\Scripts\python.exe

>>> from channels import WhatsAppWebAdapter
>>> result = WhatsAppWebAdapter.send({
...     "phone": "+919876543210",
...     "body": "Test message from automation"
... })
>>> print(result)
```

### **Test Database Connection**

```python
# Python console
>>> from database import SessionLocal
>>> from models import Lead, Message
>>> db = SessionLocal()
>>> leads = db.query(Lead).all()
>>> print(f"Total leads: {len(leads)}")
```

### **Test AI Response**

```python
>>> from ai import get_ai_response
>>> response = get_ai_response(
...     message_text="I want to learn Digital Marketing",
...     system_prompt="You are a course sales expert."
... )
>>> print(response)
```

---

## 📊 Complete Workflows

### **Workflow 1: New Lead from Website Form**

```
STEP 1: Form Submission
→ Student fills: Name, Phone, Course Interest
→ Website JavaScript calls webhook

STEP 2: API Receives
POST http://127.0.0.1:8000/inbound-message
{
  "phone_number": "+919876543210",
  "contact_name": "Priya Sharma",
  "message_text": "Interested in Web Development course",
  "channel": "whatsapp_web"
}

STEP 3: Database Operations
→ Check if Company exists → Create if not
→ Check if Pipeline exists → Create with 5 stages
→ Check if Lead exists by phone → Create/Update
→ Create LeadContact record
→ Save inbound Message
→ Create Event (message.received)

STEP 4: Job Enqueueing
→ Generate idempotency key: ai_engage_{lead_id}_{message_id}
→ Create Job record (priority: 100, status: queued)
→ Enqueue to Celery: ai.engage.apply_async()

STEP 5: Worker Processes
→ Celery picks job from Redis queue
→ Update Job status: processing
→ Execute ai_engage task

STEP 6: AI Processing
→ Fetch Lead details
→ Get AIModel configuration
→ Search AIKBDoc for course info
→ Build conversation history
→ Call OpenAI API
→ Get response: "Hi Priya! Our Web Development course is perfect for you..."

STEP 7: WhatsApp Web Send
→ Route to WhatsAppWebAdapter
→ Open Chrome (Playwright)
→ Check login → Navigate to chat
→ Type message character by character (human-like)
→ Press Enter
→ Wait for confirmation

STEP 8: Result Logging
→ Save outbound Message (direction: outbound)
→ Create Event (message.sent)
→ Update Job status: completed
→ Store external_id

STEP 9: Follow-up Scheduling
→ If no response in 24h
→ Enqueue followup_bumpup (priority: 95)
```

### **Workflow 2: Manual Follow-up**

```powershell
# Trigger follow-up for a specific lead
$body = @{
    phone_number = "+919876543210"
    contact_name = "Priya Sharma"
    message_text = "Following up on your interest"
    channel = "whatsapp_web"
} | ConvertTo-Json

Invoke-WebRequest -Method POST `
  -Uri "http://127.0.0.1:8000/inbound-message" `
  -ContentType "application/json" `
  -Body $body
```

### **Workflow 3: Replay Failed Jobs**

```powershell
# Check failed jobs
docker exec -it ai-auto-postgres psql -U ai -d ai_automation -c "SELECT * FROM jobs WHERE status='failed';"

# Replay up to 10 failed jobs
$body = '{"max_jobs":10}'
Invoke-WebRequest -Method POST `
  -Uri "http://127.0.0.1:8000/admin/dlq/replay" `
  -ContentType "application/json" `
  -Body $body
```

---

## 📁 File Structure

```
ai-auto/
│
├── main.py                      # FastAPI application & endpoints
├── worker.py                    # Celery tasks (6 background jobs)
├── models.py                    # SQLAlchemy models (16 tables)
├── database.py                  # Database connection & session
├── schemas.py                   # Pydantic request/response schemas
├── queue_manager.py             # Priority queue & job management
├── channels.py                  # Multi-channel routing (WhatsApp/Email)
├── celery_app.py               # Celery configuration
├── ai.py                        # OpenAI API integration
├── rules.py                     # Business logic & rules
│
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker services configuration
├── .env                         # Environment variables
├── .env.docker                  # Docker environment template
│
├── start.ps1                    # Start API server
├── start-worker.ps1            # Start Celery worker
├── start-all.ps1               # Start all services
│
├── README.md                    # Project overview
├── CHANGELOG.md                 # Implementation history (2000+ lines)
├── QUICKSTART.md               # Quick setup guide
├── USAGE.md                     # API usage documentation
├── DEVELOPER_GUIDE.md          # Code architecture guide
├── DOCKER_SETUP.md             # Docker installation guide
├── WHATSAPP_WEB_GUIDE.md       # WhatsApp Web automation guide
├── COMPLETE_REFERENCE.md       # This file (all commands)
│
└── whatsapp_session/           # Playwright session storage (auto-created)
    └── [browser data]
```

### **Key Files Explained**

| File | Purpose | When to Edit |
|------|---------|--------------|
| `main.py` | REST API endpoints | Add new endpoints |
| `worker.py` | Background tasks | Add new tasks |
| `models.py` | Database schema | Add tables/columns |
| `channels.py` | Message routing | Add new channels |
| `queue_manager.py` | Job queue | Change priorities |
| `ai.py` | AI integration | Change AI model |
| `.env` | Configuration | Add API keys |

---

## ⚙️ Configuration Guide

### **1. OpenAI Configuration**

Get API key: https://platform.openai.com/api-keys

```bash
# .env
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### **2. WhatsApp Web Configuration**

```bash
# .env
WHATSAPP_SESSION_DIR=./whatsapp_session
ENV=development  # or production
```

**First-time setup:**
- Run a test message
- Chrome opens automatically
- Scan QR code with phone
- Session saved (never scan again)

### **3. WhatsApp Cloud API (Optional)**

Get credentials: https://developers.facebook.com/apps

```bash
# .env
WHATSAPP_CLOUD_PHONE_ID=your-phone-number-id
WHATSAPP_CLOUD_TOKEN=your-access-token
```

### **4. Email SMTP (Optional)**

**Gmail Example:**
```bash
# .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

**Generate App Password:** https://myaccount.google.com/apppasswords

### **5. Database Configuration**

```bash
# Production (Docker)
DATABASE_URL=postgresql://ai:ai@localhost:5432/ai_automation

# Development (SQLite)
DATABASE_URL=sqlite:///./test.db
```

### **6. Celery Configuration**

```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 🎯 Quick Command Reference

### **Daily Operations**

```powershell
# Start everything
.\start-all.ps1      # Docker services
.\start.ps1          # API (Terminal 1)
.\start-worker.ps1   # Worker (Terminal 2)

# Check status
docker ps
curl http://127.0.0.1:8000/queue/stats

# Stop everything
# Close Terminal 1 & 2 (Ctrl+C)
docker compose down
```

### **Development Commands**

```powershell
# Install new package
.\.venv\Scripts\pip.exe install package-name
.\.venv\Scripts\pip.exe freeze > requirements.txt

# Database migrations (when you change models.py)
# Restart API - tables auto-create

# View logs
docker logs -f ai-auto-postgres
docker logs -f ai-auto-redis

# Clear Redis queue
docker exec ai-auto-redis redis-cli FLUSHALL
```

### **Production Deployment**

```powershell
# Set production mode
# Edit .env: ENV=production

# Edit channels.py: headless=True

# Increase delays
# Edit channels.py: base_delay=60

# Run without reload
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📚 Additional Resources

### **Documentation Files**
- **CHANGELOG.md** - Complete implementation history
- **QUICKSTART.md** - 5-minute setup guide
- **USAGE.md** - API usage examples
- **DEVELOPER_GUIDE.md** - Architecture deep dive
- **DOCKER_SETUP.md** - Docker troubleshooting
- **WHATSAPP_WEB_GUIDE.md** - WhatsApp automation details

### **External Links**
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Celery Docs**: https://docs.celeryproject.org/
- **Playwright Docs**: https://playwright.dev/python/
- **OpenAI API**: https://platform.openai.com/docs/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Redis Docs**: https://redis.io/docs/

---

## 🆘 Troubleshooting Quick Fixes

### **Issue: "Docker not found"**
```powershell
# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
docker --version
```

### **Issue: "Port 8000 already in use"**
```powershell
# Kill existing process
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

### **Issue: "WhatsApp Web login required"**
```powershell
# Delete session and re-scan QR
Remove-Item -Recurse -Force .\whatsapp_session\
# Run test message again
```

### **Issue: "Redis connection refused"**
```powershell
# Start Redis
docker compose up -d redis
# Verify
docker exec ai-auto-redis redis-cli ping
```

### **Issue: "Database connection error"**
```powershell
# Check PostgreSQL
docker ps | Select-String postgres
docker exec ai-auto-postgres pg_isready -U ai
```

---

## 🎉 You're All Set!

This complete reference guide covers:
- ✅ All 15+ libraries and tools
- ✅ Complete architecture and workflows
- ✅ 100+ commands for every operation
- ✅ Step-by-step setup instructions
- ✅ Testing and troubleshooting guides
- ✅ Configuration for all services

**Your AI Course Selling Bot is ready to:**
- 🤖 Auto-respond with AI (GPT-4)
- 💬 Send WhatsApp like a human
- 📧 Send emails automatically
- 📊 Track leads in CRM
- 🔄 Auto follow-up until conversion
- 🎯 Convert website visitors to customers

**Start selling courses now!** 🚀

---

**Version:** 1.0.0  
**Last Updated:** January 16, 2026  
**Project:** SHVYA AI Auto  
**Status:** Production Ready ✅
