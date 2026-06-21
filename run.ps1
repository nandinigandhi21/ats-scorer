# run.ps1
# Startup script for ATS Resume Scorer

# 1. Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "==========================================================" -ForegroundColor Yellow
    Write-Host " WARNING: .env file not found!" -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Yellow
    Write-Host "We have copied '.env.example' to '.env' for you." -ForegroundColor Gray
    Write-Host "Please edit the '.env' file in your project root and add" -ForegroundColor Gray
    Write-Host "your Supabase and Groq API keys before running the app." -ForegroundColor Gray
    Copy-Item .env.example .env
    start notepad .env
    exit
}

# 2. Check if virtual environment exists
if (-not (Test-Path "ai-resume\Scripts\activate.ps1")) {
    Write-Host "Error: Virtual environment 'ai-resume' not found." -ForegroundColor Red
    exit
}

# 3. Launch the Backend API (FastAPI) in a new PowerShell window
Write-Host "Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; .\\ai-resume\\Scripts\\activate.ps1; uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

# 4. Launch the Frontend UI (Streamlit) in a new PowerShell window
Write-Host "Starting Streamlit Frontend on http://localhost:8501..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; .\\ai-resume\\Scripts\\activate.ps1; streamlit run frontend/streamlit_app.py"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Both servers are starting up in separate windows!" -ForegroundColor Cyan
Write-Host " - Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host " - Frontend UI: http://localhost:8501" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
