#!/usr/bin/env python3
"""
Cross-platform TaskMaster Backend Restart Script
NO EMOJIS
"""
import os
import sys
import time
import socket
import subprocess
import psutil
from pathlib import Path

def find_free_port(start_port=8000, max_port=8020):
    """Find the first available port in the given range"""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    return start_port  # Fallback

def kill_uvicorn_processes():
    """Kill all uvicorn processes that are running TaskMaster"""
    killed_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if it's uvicorn
            if 'uvicorn' in proc.info['name'].lower():
                # Check if it's running our app
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'src.api.app:app' in cmdline or 'taskmaster' in cmdline.lower():
                    print(f"Killing uvicorn process: PID {proc.info['pid']}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return killed_count

def kill_node_processes():
    """Kill node.js development servers (optional)"""
    killed_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'node' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                # Look for Vite dev server or similar
                if 'vite' in cmdline.lower() or '5173' in cmdline:
                    print(f"Killing node process: PID {proc.info['pid']}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return killed_count

def kill_python_processes():
    """Kill python.exe processes running TaskMaster (except current process)"""
    killed_count = 0
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip current process
            if proc.info['pid'] == current_pid:
                continue
                
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                # Look for TaskMaster-related processes
                if any(keyword in cmdline.lower() for keyword in [
                    'src.api.app:app', 'uvicorn', 'taskmaster', 
                    'telegram_service', 'reminder_worker', 'app.py'
                ]):
                    print(f"Killing python process: PID {proc.info['pid']} - {cmdline}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return killed_count

def start_backend_server(port=8000):
    """Start the backend server on the specified port"""
    backend_dir = Path(__file__).parent
    
    cmd = [
        sys.executable, 
        '-m', 'uvicorn', 
        'src.api.app:app',
        '--reload',
        '--host', '0.0.0.0',
        '--port', str(port)
    ]
    
    print(f"Starting backend server on port {port}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {backend_dir}")
    
    if os.name == 'nt':
        # Windows - open in new console
        subprocess.Popen(
            cmd,
            cwd=backend_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # Unix/Linux/Mac - run in background
        subprocess.Popen(
            cmd,
            cwd=backend_dir,
        )

def main():
    """Main restart function"""
    print("=== TaskMaster Backend Restart Script ===")
    print()
    
    # Step 1: Kill existing processes
    print("Step 1: Cleaning up existing processes")
    uvicorn_killed = kill_uvicorn_processes()
    if uvicorn_killed > 0:
        print(f"- Killed {uvicorn_killed} uvicorn processes")
    else:
        print("- No uvicorn processes found")
    
    # Kill node processes to prevent duplicate frontend instances
    node_killed = kill_node_processes()
    if node_killed > 0:
        print(f"- Killed {node_killed} node processes")
    else:
        print("- No node processes found")
    
    # Kill python processes to prevent Telegram/worker conflicts
    python_killed = kill_python_processes()
    if python_killed > 0:
        print(f"- Killed {python_killed} python processes")
    else:
        print("- No conflicting python processes found")
    
    # Wait for processes to fully terminate
    if uvicorn_killed > 0 or node_killed > 0 or python_killed > 0:
        print("- Waiting for processes to terminate...")
        time.sleep(3)  # Longer wait for python processes
    
    # Step 2: Find available port
    print("\nStep 2: Finding available port")
    port = find_free_port()
    print(f"- Using port {port}")
    
    # Step 3: Start new server
    print(f"\nStep 3: Starting new backend server")
    start_backend_server(port)
    
    print(f"\n[OK] Backend server starting on port {port}")
    print(f"  - Base URL: http://localhost:{port}")
    print(f"  - Health Check: http://localhost:{port}/health")
    print(f"  - API Docs: http://localhost:{port}/docs")
    print(f"  - Restart Endpoint: http://localhost:{port}/api/restart")
    
    # Wait a moment to see if server starts
    print("\nWaiting 3 seconds to verify startup...")
    time.sleep(3)
    
    # Check if server is responding
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            if result == 0:
                print(f"[OK] Server is responding on port {port}")
            else:
                print(f"[WARNING] Server may not be ready yet on port {port}")
    except Exception as e:
        print(f"[WARNING] Could not verify server status: {e}")
    
    print("\nRestart complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nRestart cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during restart: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)