#!/usr/bin/env python3
"""
Debug what processes are detected as TaskMaster
NO EMOJIS
"""
import psutil
import socket

def debug_existing_backend():
    """Debug what check_for_existing_taskmaster_backend finds"""
    print("=== DEBUGGING EXISTING BACKEND DETECTION ===")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            name = proc.info['name']
            
            # Same logic as in restart.py
            is_taskmaster = ('uvicorn' in cmdline and 'src.api.app:app' in cmdline) or 'taskmaster' in cmdline.lower()
            
            if is_taskmaster:
                print(f"FOUND TaskMaster process:")
                print(f"  PID: {proc.info['pid']}")
                print(f"  Name: {name}")
                print(f"  Command: {cmdline}")
                print()
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    print("=== PORT 8000 CHECK ===")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            result = s.connect_ex(('localhost', 8000))
            if result == 0:
                print("Port 8000 responds to connection")
            else:
                print(f"Port 8000 connection failed with code: {result}")
        except Exception as e:
            print(f"Port 8000 check error: {e}")

if __name__ == "__main__":
    debug_existing_backend()