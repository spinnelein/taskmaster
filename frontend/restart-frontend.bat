@echo off
echo === TaskMaster Frontend Restart Script ===

:: Kill existing node processes
echo Stopping existing node.js processes...
taskkill /f /im node.exe > nul 2>&1
if %errorlevel% == 0 (
    echo - Killed node.js processes
) else (
    echo - No node.js processes found
)

:: Wait a moment for processes to fully terminate
timeout /t 2 /nobreak > nul

:: Find available port starting from 5173
set PORT=5173
:FIND_PORT
netstat -an | find ":%PORT%" > nul
if %errorlevel% == 0 (
    set /a PORT+=1
    if %PORT% lss 5180 goto FIND_PORT
)

echo Starting frontend server on port %PORT%...

:: Change to frontend directory
cd /d "%~dp0"

:: Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

:: Start the development server
start "TaskMaster Frontend - Port %PORT%" cmd /k "npm run dev -- --port %PORT%"

echo.
echo Frontend development server started on port %PORT%
echo Console window opened for server logs
echo.
echo To access the application:
echo   - Frontend URL: http://localhost:%PORT%
echo   - With hot module replacement enabled
echo.
echo Make sure your backend is running on port 8002 or update the API configuration.
echo.
pause