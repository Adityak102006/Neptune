@echo off
setlocal enabledelayedexpansion
title Neptune — Image Similarity Search
color 0B

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║       🔱  N E P T U N E                 ║
echo   ║    Local Image Similarity Search         ║
echo   ╚══════════════════════════════════════════╝
echo.

:: ── Check Python ──────────────────────────────────────
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ from https://python.org
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: ── Create virtual environment if needed ──────────────
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: ── Activate venv and install Python dependencies ─────
call venv\Scripts\activate.bat

echo [2/4] Installing Python dependencies (first run may take a few minutes)...
pip install -r backend\requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)

:: ── Build frontend if needed ──────────────────────────
if not exist "frontend\dist\index.html" (
    where node >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Node.js not found. Please install Node.js 18+ from https://nodejs.org
        pause
        exit /b 1
    )

    echo [3/4] Building frontend (first run only)...
    cd frontend
    call npm install --silent
    call npm run build
    cd ..

    if not exist "frontend\dist\index.html" (
        echo [ERROR] Frontend build failed.
        pause
        exit /b 1
    )
) else (
    echo [3/4] Frontend already built. Skipping.
)

:: ── Start the server ──────────────────────────────────
echo [4/4] Starting Neptune server...
echo.
echo   ★  Neptune is running at: http://localhost:8000
echo   ★  Press Ctrl+C to stop the server.
echo.

:: Open browser after a short delay
start "" http://localhost:8000

:: Run the server (blocks until Ctrl+C)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

:: Cleanup
call venv\Scripts\deactivate.bat 2>nul
echo.
echo Neptune stopped. Goodbye!
pause
