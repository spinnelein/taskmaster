#!/usr/bin/env python3
"""
Force cleanup all TaskMaster processes
NO EMOJIS
"""
import psutil
import os

def force_kill_all_taskmaster():
    """Force kill ALL TaskMaster processes"""
    killed_count = 0
    current_pid = os.getpid()
    
    print("=== FORCE CLEANUP ALL TASKMASTER PROCESSES ===")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip current process
            if proc.info['pid'] == current_pid:
                continue
                
            name = proc.info['name'].lower()
            cmdline = ' '.join(proc.info['cmdline'] or []).lower()
            
            # Kill any process that might be TaskMaster related
            should_kill = (
                # Python processes running uvicorn or TaskMaster
                ('python' in name and any(keyword in cmdline for keyword in [
                    'src.api.app:app', 'uvicorn', 'taskmaster', 
                    'telegram_service', 'reminder_worker', 'app.py',
                    'telegram', 'getUpdates'
                ])) or
                # Uvicorn processes
                ('uvicorn' in name and ('taskmaster' in cmdline or 'src.api.app' in cmdline)) or
                # Node processes for frontend
                ('node' in name and any(keyword in cmdline for keyword in [
                    'vite', 'npm run dev', 'frontend/src', 'taskmaster', '5173'
                ])) or
                # Any python process in TaskMaster directory
                ('python' in name and 'taskmaster' in cmdline) or
                # Aggressive: multiprocessing.spawn processes (likely from TaskMaster services)
                ('python' in name and 'multiprocessing.spawn' in cmdline)
            )
            
            # Debug: Print all python processes to see what they are
            if 'python' in name:
                print(f"DEBUG: Python process PID {proc.info['pid']}: {cmdline[:100]}...")
            
            if should_kill:
                try:
                    print(f"Force killing: PID {proc.info['pid']} ({name})")
                    print(f"  Command: {cmdline[:80]}...")
                    proc.kill()
                    killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    print(f"  Failed to kill: {e}")
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    print(f"\nForce killed {killed_count} TaskMaster processes")
    return killed_count

if __name__ == "__main__":
    force_kill_all_taskmaster()
    print("\nAll TaskMaster processes should now be terminated.")
    print("You can now run 'python restart.py' to start a fresh single instance.")