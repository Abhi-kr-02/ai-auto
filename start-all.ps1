# SHVYA AI Auto - Start All Services Script
# This script starts Redis, PostgreSQL (via Docker), FastAPI server, and Celery worker

Write-Host "`n=== SHVYA AI Auto - Starting All Services ===" -ForegroundColor Cyan

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  Docker not found. Skipping PostgreSQL and Redis startup." -ForegroundColor Yellow
    Write-Host "   Starting with SQLite instead..." -ForegroundColor Yellow
} else {
    Write-Host "✅ Starting PostgreSQL and Redis via Docker..." -ForegroundColor Green
    docker compose up -d
    
    Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host "✅ Docker services started" -ForegroundColor Green
}

Write-Host "`n📋 Services Status:" -ForegroundColor Cyan
Write-Host "   - Database: SQLite/PostgreSQL" -ForegroundColor White
Write-Host "   - Redis: localhost:6379" -ForegroundColor White
Write-Host "   - API Server: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   - Celery Worker: Active" -ForegroundColor White
Write-Host ""

Write-Host "🚀 To start services in separate terminals:" -ForegroundColor Yellow
Write-Host "   Terminal 1: .\start.ps1 (API Server)" -ForegroundColor White
Write-Host "   Terminal 2: .\start-worker.ps1 (Celery Worker)" -ForegroundColor White
Write-Host ""
Write-Host "📚 API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Magenta
Write-Host ""
