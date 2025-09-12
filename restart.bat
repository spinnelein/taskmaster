@echo off
echo Restarting TaskMaster server...
python dev_restart.py
echo.
echo Server restart initiated. Check http://localhost:8000/health
pause