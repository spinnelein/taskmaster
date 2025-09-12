#!/usr/bin/env python3
"""
Development server restart utility
Kills existing server process and starts a new one
NO EMOJIS
"""

import os
import sys
import subprocess
import signal
import psutil
import time

def find_server_process():
    """Find the uvicorn server process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'uvicorn' in ' '.join(cmdline) and 'src.api.app:app' in ' '.join(cmdline):
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def restart_server():
    """Restart the development server"""
    print("Looking for running server...")
    
    # Find and kill existing server
    pid = find_server_process()
    if pid:
        print(f"Found server process (PID: {pid}), stopping it...")
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
        except ProcessLookupError:
            print("Process already stopped")
    else:
        print("No running server found")
    
    # Start new server
    print("Starting new server...")
    os.chdir("backend")
    
    # Start the server in the background
    cmd = [sys.executable, "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    
    # On Windows, use CREATE_NEW_PROCESS_GROUP to allow it to run independently
    if os.name == 'nt':
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        subprocess.Popen(cmd)
    
    print("Server restart initiated")
    print("Check http://localhost:8000/health in a few seconds")

if __name__ == "__main__":
    restart_server()