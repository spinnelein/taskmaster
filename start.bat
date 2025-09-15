@echo off
setlocal enabledelayedexpansion
echo === TaskMaster Fast Startup Script ===
echo.

:: Find available backend port (8000-8020)
set BACKEND_PORT=8000
:FIND_BACKEND_PORT
netstat -an | find ":%BACKEND_PORT%" > nul
if %errorlevel% == 0 (
    set /a BACKEND_PORT+=1
    if %BACKEND_PORT% lss 8021 goto FIND_BACKEND_PORT
)

:: Find available frontend port (5173-5180)
set FRONTEND_PORT=5173
:FIND_FRONTEND_PORT
netstat -an | find ":%FRONTEND_PORT%" > nul
if %errorlevel% == 0 (
    set /a FRONTEND_PORT+=1
    if %FRONTEND_PORT% lss 5181 goto FIND_FRONTEND_PORT
)

echo Starting TaskMaster services...
echo - Backend will use port %BACKEND_PORT%
echo - Frontend will use port %FRONTEND_PORT%
echo.

:: Start Backend (uvicorn with FastAPI app)
echo Starting backend server...
cd /d "%~dp0backend"
start "TaskMaster Backend - Port %BACKEND_PORT%" cmd /k "uvicorn src.api.app:app --reload --host 0.0.0.0 --port %BACKEND_PORT%"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak > nul

:: Start Frontend (npm dev server)
echo Starting frontend server...
cd /d "%~dp0frontend"

:: Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

start "TaskMaster Frontend - Port %FRONTEND_PORT%" cmd /k "npm run dev -- --port %FRONTEND_PORT%"

echo.
echo === TaskMaster Started Successfully ===
echo.
echo Access your application:
echo   - Frontend: http://localhost:%FRONTEND_PORT%
echo   - Backend:  http://localhost:%BACKEND_PORT%
echo   - API Docs: http://localhost:%BACKEND_PORT%/docs
echo   - Health:   http://localhost:%BACKEND_PORT%/health
echo.
echo Both services are running in separate console windows.
echo Use kill.bat to stop all services.
echo.
pause