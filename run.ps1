Write-Host "========================================================" -ForegroundColor Yellow
Write-Host "  Launching Crypto Screener: FastAPI + Next.js" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Yellow

# Launch backend in separate window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "if (Test-Path '.\.venv\Scripts\python.exe') { & '.\.venv\Scripts\python.exe' app.py } else { python app.py }"

# Launch Next.js frontend in current window
Write-Host "Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Cyan
Set-Location frontend
npm run dev
