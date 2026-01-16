# SHVYA AI Auto - Start Celery Worker Script
# This script starts the Celery worker for processing queue jobs

Write-Host "`n=== SHVYA AI Auto - Starting Celery Worker ===" -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "   Run: python -m venv .venv" -ForegroundColor White
    exit 1
}

# Check if Redis is running
Write-Host "🔍 Checking Redis connection..." -ForegroundColor Yellow
try {
    $redis = New-Object System.Net.Sockets.TcpClient("localhost", 6379)
    $redis.Close()
    Write-Host "✅ Redis is running on localhost:6379" -ForegroundColor Green
} catch {
    Write-Host "❌ Redis is not running!" -ForegroundColor Red
    Write-Host "   Please start Redis first:" -ForegroundColor White
    Write-Host "   - Using Docker: docker compose up -d redis" -ForegroundColor White
    Write-Host "   - Or install Redis locally" -ForegroundColor White
    exit 1
}

# Load environment variables from .env
if (Test-Path ".env") {
    Write-Host "✅ Loading environment variables from .env..." -ForegroundColor Green
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

Write-Host "✅ Starting Celery worker..." -ForegroundColor Green
Write-Host "   Processing tasks with priorities:" -ForegroundColor White
Write-Host "   - P1 (90-100): ai.engage, followup.bumpup, ai.summary" -ForegroundColor Cyan
Write-Host "   - P2 (50-70): sequence.step, email.sequence, webhook.reminder" -ForegroundColor Cyan
Write-Host ""

# Start Celery worker (use --pool=solo on Windows)
& ".\.venv\Scripts\celery.exe" -A worker worker --loglevel=info --pool=solo --concurrency=4

Write-Host "`n✅ Worker stopped" -ForegroundColor Green
