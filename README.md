# AI Automation Project

## ✅ Dependencies Installed

All Python dependencies have been installed successfully:
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL driver (psycopg2-binary)
- Celery
- Redis client
- OpenAI
- Pydantic

## 🚀 Setup Required

### 1. OpenAI API Key Configuration

You need to configure your OpenAI API key. You have **two options**:

#### Option A: Using .env file (Recommended - Easiest)
1. Copy `env.example` to `.env`:
   ```powershell
   Copy-Item env.example .env
   ```
2. Edit `.env` and add your API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```
   Get your API key from: https://platform.openai.com/api-keys

#### Option B: Environment Variable
Set it in your terminal before running:
```powershell
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Windows CMD
set OPENAI_API_KEY=sk-your-api-key-here
```

**Note:** The API key is loaded in `app/ai.py` - it will automatically read from `.env` file or environment variable.

### 2. Database & Redis Services

The project requires **PostgreSQL** and **Redis** to be running.

#### Option A: Using Docker (Recommended)
```bash
docker compose up -d
```

#### Option B: Install Locally
- **PostgreSQL**: Install from https://www.postgresql.org/download/windows/
  - Create database: `ai_automation`
  - User: `ai`
  - Password: `ai`
  - Port: `5432`

- **Redis**: Install from https://redis.io/download or use WSL
  - Port: `6379`

### 3. Database Configuration

The database connection is configured in `app/database.py`:
- Host: `localhost`
- Port: `5432`
- Database: `ai_automation`
- User: `ai`
- Password: `ai`

## 🏃 Running the Application

### Quick Start (Using PowerShell Scripts)

1. **Start Docker Desktop** manually from Start Menu (wait until it's fully running)

2. **Set your OpenAI API key**:
   ```powershell
   $env:OPENAI_API_KEY="your-api-key-here"
   ```

3. **Terminal 1 - Start FastAPI Server**:
   ```powershell
   .\start.ps1
   ```
   This script will:
   - Wait for Docker to be ready
   - Start Redis and PostgreSQL containers
   - Start the FastAPI server

4. **Terminal 2 - Start Celery Worker**:
   ```powershell
   .\start-worker.ps1
   ```

### Manual Start

**Terminal 1: Start FastAPI Server**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Start Celery Worker**
```bash
celery -A worker worker --loglevel=info
```

## 📡 API Endpoints

Once running, access:
- **API Docs**: http://localhost:8000/docs
- **Inbound Message Endpoint**: POST http://localhost:8000/inbound-message

### Example Request:
```json
{
  "phone": "+1234567890",
  "text": "Hello, I'm interested in your product"
}
```

## 📝 Notes

- The database tables will be created automatically on first run
- Make sure Redis and PostgreSQL are running before starting the application
- The Celery worker processes AI engagement tasks asynchronously
