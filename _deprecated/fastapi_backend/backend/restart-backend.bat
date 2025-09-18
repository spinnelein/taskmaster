@echo off
echo === TaskMaster Backend Restart Script ===

:: Kill all uvicorn processes
echo Stopping existing uvicorn processes...
taskkill /f /im uvicorn.exe > nul 2>&1
if %errorlevel% == 0 (
    echo - Killed uvicorn processes
) else (
    echo - No uvicorn processes found
)

:: Wait a moment for processes to fully terminate
timeout /t 2 /nobreak > nul

:: Find available port starting from 8000
set PORT=8000
:FIND_PORT
netstat -an | find ":%PORT%" > nul
if %errorlevel% == 0 (
    set /a PORT+=1
    if %PORT% lss 8010 goto FIND_PORT
)

echo Starting backend server on port %PORT%...

:: Change to backend directory
cd /d "%~dp0"

:: Start the server with auto-reload
start "TaskMaster Backend - Port %PORT%" cmd /k "uvicorn src.api.app:app --reload --host 0.0.0.0 --port %PORT%"

echo.
echo Backend server started on port %PORT%
echo Console window opened for server logs
echo.
echo To access the API:
echo   - Base URL: http://localhost:%PORT%
echo   - Health Check: http://localhost:%PORT%/health
echo   - API Docs: http://localhost:%PORT%/docs
echo   - Restart Endpoint: http://localhost:%PORT%/api/restart
echo.
pause