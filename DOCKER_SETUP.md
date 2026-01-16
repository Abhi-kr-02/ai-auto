# Docker Setup Guide - SHVYA AI Auto

## ✅ Docker Desktop Installation Complete!

Docker Desktop has been installed on your system. Follow these steps to complete the setup.

---

## 🚀 Quick Start

### Step 1: Start Docker Desktop

1. Open **Docker Desktop** from Start Menu
2. Accept the service agreement if prompted
3. Wait for Docker to fully start (look for the **green whale icon** in system tray)
4. This may take 2-3 minutes on first launch

### Step 2: Verify Installation

Open a **NEW PowerShell window** and run:

```powershell
docker --version
docker ps
```

You should see:
```
Docker version 4.56.0
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

### Step 3: Start All Services

```powershell
cd E:\ai-auto
.\start-all.ps1
```

This will:
- Start PostgreSQL database (port 5432)
- Start Redis message broker (port 6379)
- Display service status

### Step 4: Start API and Worker

**Terminal 1** - API Server:
```powershell
.\start.ps1
```

**Terminal 2** - Celery Worker:
```powershell
.\start-worker.ps1
```

---

## 🐳 Docker Services

### PostgreSQL Database
- **Image**: postgres:15
- **Port**: 5432
- **Database**: ai_automation
- **Username**: ai
- **Password**: ai

**Connection String**:
```
postgresql://ai:ai@localhost:5432/ai_automation
```

### Redis Message Broker
- **Image**: redis:7-alpine
- **Port**: 6379

**Connection String**:
```
redis://localhost:6379/0
```

---

## 🔧 Docker Commands

### Start Services
```powershell
docker compose up -d
```

### Stop Services
```powershell
docker compose down
```

### View Logs
```powershell
# All services
docker compose logs -f

# Specific service
docker logs ai-auto-postgres
docker logs ai-auto-redis
```

### Check Status
```powershell
docker ps
```

### Access PostgreSQL
```powershell
docker exec -it ai-auto-postgres psql -U ai -d ai_automation
```

Common queries:
```sql
-- View all tables
\dt

-- Check leads
SELECT * FROM leads LIMIT 10;

-- Check jobs
SELECT * FROM jobs ORDER BY created_at DESC LIMIT 20;

-- Check messages
SELECT * FROM messages ORDER BY created_at DESC LIMIT 10;
```

### Access Redis
```powershell
docker exec -it ai-auto-redis redis-cli
```

Common commands:
```
PING
KEYS *
LLEN celery
INFO
```

---

## 🛠️ Troubleshooting

### Docker Desktop Not Starting

**Problem**: Docker Desktop won't start or shows error

**Solutions**:
1. Restart your computer
2. Enable Hyper-V in Windows Features:
   - Open Control Panel
   - Programs → Turn Windows features on or off
   - Check "Hyper-V" and "Containers"
   - Restart
3. Enable WSL 2:
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```

### Docker Command Not Found

**Problem**: `docker: command not found`

**Solutions**:
1. Close and reopen PowerShell/Terminal
2. Restart your computer
3. Add Docker to PATH manually:
   - Open System Environment Variables
   - Add: `C:\Program Files\Docker\Docker\resources\bin`

### Port Already in Use

**Problem**: `port 5432 already allocated` or `port 6379 already allocated`

**Solutions**:
```powershell
# Check what's using the port
Get-NetTCPConnection -LocalPort 5432
Get-NetTCPConnection -LocalPort 6379

# Stop existing containers
docker compose down

# Or change ports in docker-compose.yml
```

### Container Won't Start

**Problem**: Container exits immediately

**Solutions**:
```powershell
# Check logs
docker logs ai-auto-postgres
docker logs ai-auto-redis

# Remove and recreate
docker compose down -v
docker compose up -d
```

---

## 📊 Monitoring

### Health Checks

Check if services are healthy:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Expected output:
```
NAMES               STATUS
ai-auto-postgres    Up 5 minutes (healthy)
ai-auto-redis       Up 5 minutes (healthy)
```

### Resource Usage

```powershell
docker stats
```

Shows CPU, memory, and network usage for containers.

---

## 🔄 Database Migration from SQLite to PostgreSQL

If you were using SQLite (test.db) before:

### Option 1: Fresh Start (Recommended)
```powershell
# Stop everything
docker compose down -v

# Remove SQLite database
Remove-Item test.db -ErrorAction SilentlyContinue

# Update .env to use PostgreSQL
# DATABASE_URL=postgresql://ai:ai@localhost:5432/ai_automation

# Start fresh
docker compose up -d
.\start.ps1
```

### Option 2: Migrate Data
```powershell
# Export from SQLite
.\.venv\Scripts\python.exe -c "
from database import SessionLocal, Base, engine as sqlite_engine
from models import *
import json

db = SessionLocal()
# Export logic here
"

# Import to PostgreSQL
# (Manual process - export to JSON, then import)
```

---

## 🎯 Full Stack Architecture

```
┌─────────────────────────────────────────┐
│        External Systems                 │
│  (WhatsApp, Email, Webhooks, etc.)     │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│     FastAPI Server (port 8000)          │
│  - REST API endpoints                   │
│  - Auto-creation logic                  │
│  - Job enqueueing                       │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│   PostgreSQL (Docker - port 5432)       │
│  - 16 database tables                   │
│  - Job records                          │
│  - Event sourcing                       │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│     Redis (Docker - port 6379)          │
│  - Celery message broker                │
│  - Priority queue                       │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│    Celery Worker (6 tasks)              │
│  - ai.engage (P1)                       │
│  - followup.bumpup (P1)                 │
│  - ai.summary (P1)                      │
│  - sequence.step (P2)                   │
│  - email.sequence (P2)                  │
│  - webhook.reminder (P2)                │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│       External APIs                     │
│  - OpenAI (GPT-4o-mini)                │
│  - WhatsApp Cloud API (TODO)           │
│  - SMTP/SES (TODO)                     │
└─────────────────────────────────────────┘
```

---

## 🎉 Success Checklist

- [ ] Docker Desktop installed and running (green whale icon)
- [ ] `docker --version` works in terminal
- [ ] `docker compose up -d` starts containers
- [ ] `docker ps` shows 2 healthy containers
- [ ] `.\start.ps1` starts API server on port 8000
- [ ] `.\start-worker.ps1` starts Celery worker
- [ ] http://127.0.0.1:8000/docs loads Swagger UI
- [ ] POST to `/inbound-message` creates lead and enqueues job
- [ ] Worker processes jobs (check Terminal 2 logs)
- [ ] Database has records (check via `docker exec`)

---

## 🆘 Need Help?

1. Check logs:
   - API: Terminal 1 output
   - Worker: Terminal 2 output
   - Database: `docker logs ai-auto-postgres`
   - Redis: `docker logs ai-auto-redis`

2. Verify connections:
   ```powershell
   # Test PostgreSQL
   docker exec -it ai-auto-postgres pg_isready -U ai
   
   # Test Redis
   docker exec -it ai-auto-redis redis-cli ping
   ```

3. Restart everything:
   ```powershell
   docker compose down
   docker compose up -d
   # Close PowerShell windows running API and worker
   .\start.ps1  # Terminal 1
   .\start-worker.ps1  # Terminal 2
   ```

---

## 📚 Next Steps

Once Docker is running:

1. **Test the API** - See [USAGE.md](USAGE.md)
2. **Understand the code** - See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
3. **Review implementation** - See [CHANGELOG.md](CHANGELOG.md)
4. **Integrate channels** - Implement TODOs in [channels.py](channels.py)

---

**Pro Tip**: Keep Docker Desktop running in the background. It will auto-start containers on system reboot if configured.
