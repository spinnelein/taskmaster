@echo off
echo === TaskMaster Process Termination ===
echo.

echo Stopping all TaskMaster processes...

:: Kill uvicorn processes (backend server + all Python services)
echo Terminating backend server (uvicorn)...
taskkill /f /im uvicorn.exe > nul 2>&1
if %errorlevel% == 0 (
    echo - Backend server stopped
) else (
    echo - No backend server found
)

:: Wait for graceful shutdown
timeout /t 2 /nobreak > nul

:: Kill node processes (frontend dev server)
echo Terminating frontend server (node.exe)...
taskkill /f /im node.exe > nul 2>&1
if %errorlevel% == 0 (
    echo - Frontend server stopped
) else (
    echo - No frontend server found
)

:: Additional cleanup for any Python processes that might be running TaskMaster services
echo Cleaning up any remaining Python services...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe"') do (
    taskkill /f /pid %%i > nul 2>&1
)

echo.
echo === All TaskMaster processes terminated ===
echo.
echo Ports 8000-8020 and 5173-5180 should now be available.
echo You can run start.bat to restart the services.
echo.
