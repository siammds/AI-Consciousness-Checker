@echo off
setlocal

:: Get the directory of the batch file
set "DIR=%~dp0"
cd /d "%DIR%"

echo ==========================================================
echo    AI Consciousness ^& Metacognition Evaluation System
echo ==========================================================
echo.
echo Starting the application...
echo.

:: Check if .venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\activate.bat
    echo Please ensure the project dependencies are installed.
    echo.
    pause
    exit /b 1
)

:: Activate virtual environment
call ".venv\Scripts\activate.bat"

:: Start Uvicorn implicitly opening the browser
echo [INFO] Server starting at http://localhost:8000
echo [INFO] Press Ctrl+C in this window to stop the server.
echo.

:: Open browser
start http://localhost:8000

:: Run the server
python -m uvicorn app.main:app --reload --port 8000

:: In case Uvicorn fails to start
pause
