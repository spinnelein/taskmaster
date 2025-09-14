@echo off
echo === TaskMaster Full Stack Restart Script ===
echo.

:: Kill existing processes
echo Step 1: Stopping existing processes...
echo - Stopping uvicorn (backend) processes...
taskkill /f /im uvicorn.exe > nul 2>&1

echo - Stopping python.exe processes...
taskkill /f /im python.exe > nul 2>&1

echo - Stopping node.js (frontend) processes...
taskkill /f /im node.exe > nul 2>&1

echo - Waiting for processes to terminate and ports to release...
timeout /t 5 /nobreak > nul

:: Find available ports
echo.
echo Step 2: Finding available ports...

:: Backend port - prefer 8000 if available
set BACKEND_PORT=8000
set PREFERRED_PORT=8000

:: Check if user specified a port
if "%1" NEQ "" (
    set PREFERRED_PORT=%1
    echo - User requested backend port %PREFERRED_PORT%
)

:: Try preferred port first
netstat -an | find ":%PREFERRED_PORT%" > nul
if %errorlevel% == 1 (
    set BACKEND_PORT=%PREFERRED_PORT%
) else (
    :: Find alternative port
    :FIND_BACKEND_PORT
    netstat -an | find ":%BACKEND_PORT%" > nul
    if %errorlevel% == 0 (
        set /a BACKEND_PORT+=1
        if %BACKEND_PORT% lss 8010 goto FIND_BACKEND_PORT
    )
)

:: Frontend port  
set FRONTEND_PORT=5173
:FIND_FRONTEND_PORT
netstat -an | find ":%FRONTEND_PORT%" > nul
if %errorlevel% == 0 (
    set /a FRONTEND_PORT+=1
    if %FRONTEND_PORT% lss 5180 goto FIND_FRONTEND_PORT
)

echo - Backend will use port %BACKEND_PORT%
echo - Frontend will use port %FRONTEND_PORT%

:: Start backend
echo.
echo Step 3: Starting backend server...
cd /d "%~dp0\backend"
start "TaskMaster Backend - Port %BACKEND_PORT%" cmd /k "python restart.py %BACKEND_PORT%"

:: Wait a moment for backend to start and write config
timeout /t 5 /nobreak > nul

:: Start frontend
echo Step 4: Starting frontend server...
cd /d "%~dp0\frontend"

:: Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

:: Set backend port environment variable for frontend
set VITE_BACKEND_PORT=%BACKEND_PORT%
start "TaskMaster Frontend - Port %FRONTEND_PORT%" cmd /k "set VITE_BACKEND_PORT=%BACKEND_PORT% && npm run dev -- --port %FRONTEND_PORT%"

:: Summary
echo.
echo ================================================
echo   TaskMaster Development Servers Started
echo ================================================
echo.
echo Backend:
echo   - URL: http://localhost:%BACKEND_PORT%
echo   - Health: http://localhost:%BACKEND_PORT%/health
echo   - API Docs: http://localhost:%BACKEND_PORT%/docs
echo   - Restart: http://localhost:%BACKEND_PORT%/api/restart
echo.
echo Frontend:
echo   - URL: http://localhost:%FRONTEND_PORT%
echo   - Development server with hot reload
echo.
echo Both servers are running in separate console windows.
echo Close this window or press Ctrl+C to exit.
echo.
echo Press any key to continue...
pause > nul