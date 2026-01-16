# SHVYA AI Auto - Start Server Script
# This script starts the FastAPI server

Write-Host "`n=== SHVYA AI Auto - Starting Server ===" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "   Create .env from env.example and add your OPENAI_API_KEY" -ForegroundColor Yellow
    Write-Host ""
}

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "   Run: python -m venv .venv" -ForegroundColor White
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

Write-Host "✅ Starting FastAPI server..." -ForegroundColor Green
Write-Host "   Server will be available at: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""

# Start the server
& ".\.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

Write-Host "`n✅ Server stopped" -ForegroundColor Green
