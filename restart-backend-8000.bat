@echo off
echo === TaskMaster Backend Restart on Port 8000 ===
echo.

:: Kill all backend processes
echo Stopping existing backend processes...
taskkill /f /im uvicorn.exe > nul 2>&1
taskkill /f /im python.exe > nul 2>&1

:: Wait for processes to terminate and port to be released
echo Waiting for port 8000 to be released...
timeout /t 8 /nobreak > nul

:: Try to claim port 8000
:CHECK_PORT
netstat -an | find ":8000" | find "LISTENING" > nul
if %errorlevel% == 0 (
    echo Port 8000 is still in use, waiting...
    timeout /t 3 /nobreak > nul
    goto CHECK_PORT
)

echo Port 8000 is available!

:: Start backend on port 8000
cd /d "%~dp0\backend"
echo Starting backend on port 8000...
python restart.py 8000

pause