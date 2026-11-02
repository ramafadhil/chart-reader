@echo off
title Crypto Volatility Screener & AI Analyst

echo ========================================================
echo   Launching Crypto Screener: FastAPI + Next.js
echo ========================================================

:: 1. Start FastAPI Backend in a separate window
start "FastAPI Backend (Port 8000)" cmd /k "if exist .venv\Scripts\python.exe (.venv\Scripts\python.exe app.py) else (python app.py)"

:: 2. Start Next.js Frontend in this window
echo Starting Next.js Frontend on http://localhost:3000...
cd frontend
npm run dev
