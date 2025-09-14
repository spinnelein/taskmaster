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
from src.api.port_config import PortConfig

def find_free_port(start_port=8000, max_port=8020, preferred_port=8000):
    """Find the first available port in the given range, preferring a specific port"""
    # Try preferred port first
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', preferred_port))
            return preferred_port
        except OSError:
            pass
    
    # If preferred port is not available, find another
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    return start_port  # Fallback

def kill_uvicorn_processes():
    """Gracefully shutdown uvicorn processes that are running TaskMaster"""
    killed_count = 0
    processes_to_terminate = []
    
    # First, collect all TaskMaster uvicorn processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if it's uvicorn
            if 'uvicorn' in proc.info['name'].lower():
                # Check if it's running our app
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'src.api.app:app' in cmdline or 'taskmaster' in cmdline.lower():
                    processes_to_terminate.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    # Try graceful termination first
    if processes_to_terminate:
        print("Attempting graceful shutdown of uvicorn processes...")
        for proc in processes_to_terminate:
            try:
                print(f"Sending SIGTERM to uvicorn process: PID {proc.info['pid']}")
                proc.terminate()  # Send SIGTERM for graceful shutdown
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Wait for graceful shutdown
        gone, alive = psutil.wait_procs(processes_to_terminate, timeout=5)
        killed_count += len(gone)
        
        # Force kill any remaining processes
        if alive:
            print("Force killing remaining uvicorn processes...")
            for proc in alive:
                try:
                    print(f"Force killing uvicorn process: PID {proc.info['pid']}")
                    proc.kill()
                    killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    
    return killed_count

def kill_node_processes():
    """Kill TaskMaster-specific node.js development servers"""
    killed_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        try:
            if 'node' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                cwd = proc.info.get('cwd', '') or ''
                
                # More specific targeting for TaskMaster-related processes
                is_taskmaster_related = any(keyword in cmdline.lower() for keyword in [
                    'vite', 'npm run dev', 'frontend/src', 'taskmaster'
                ]) or any(keyword in cwd.lower() for keyword in [
                    'taskmaster', 'frontend'
                ]) or any(port in cmdline for port in [
                    '5173', ':5173', '--port 5173'
                ])
                
                if is_taskmaster_related:
                    print(f"Killing TaskMaster node process: PID {proc.info['pid']}")
                    print(f"  Command: {cmdline[:80]}...")  # Show first 80 chars
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return killed_count

def kill_python_processes():
    """Gracefully shutdown python.exe processes running TaskMaster (except current process)"""
    killed_count = 0
    current_pid = os.getpid()
    processes_to_terminate = []
    
    # Collect TaskMaster-related Python processes
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
                    processes_to_terminate.append((proc, cmdline))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    # Try graceful termination first
    if processes_to_terminate:
        print("Attempting graceful shutdown of TaskMaster Python processes...")
        procs_to_wait = []
        
        for proc, cmdline in processes_to_terminate:
            try:
                print(f"Sending SIGTERM to python process: PID {proc.info['pid']}")
                print(f"  Command: {cmdline[:60]}...")
                proc.terminate()  # Send SIGTERM for graceful shutdown
                procs_to_wait.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Wait for graceful shutdown (longer timeout for services)
        if procs_to_wait:
            gone, alive = psutil.wait_procs(procs_to_wait, timeout=8)
            killed_count += len(gone)
            
            # Force kill any remaining processes
            if alive:
                print("Force killing remaining Python processes...")
                for proc in alive:
                    try:
                        print(f"Force killing python process: PID {proc.info['pid']}")
                        proc.kill()
                        killed_count += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
    
    return killed_count

def verify_processes_terminated():
    """Verify that all TaskMaster processes have been terminated"""
    remaining_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name'].lower()
            cmdline = ' '.join(proc.info['cmdline'] or []).lower()
            
            # Check for remaining TaskMaster processes
            is_taskmaster_process = (
                ('uvicorn' in name and ('src.api.app:app' in cmdline or 'taskmaster' in cmdline)) or
                ('node' in name and ('vite' in cmdline or 'npm run dev' in cmdline or '5173' in cmdline)) or
                ('python' in name and any(keyword in cmdline for keyword in [
                    'src.api.app:app', 'uvicorn', 'taskmaster', 
                    'telegram_service', 'reminder_worker'
                ]))
            )
            
            if is_taskmaster_process and proc.info['pid'] != os.getpid():
                remaining_processes.append((proc.info['pid'], name, cmdline[:60]))
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if remaining_processes:
        print(f"[WARNING] Found {len(remaining_processes)} remaining TaskMaster processes:")
        for pid, name, cmdline in remaining_processes:
            print(f"  - PID {pid} ({name}): {cmdline}...")
        return False
    else:
        print("[OK] All TaskMaster processes have been terminated")
        return True

def start_backend_server(port=8000):
    """Start the backend server on the specified port"""
    backend_dir = Path(__file__).parent
    
    # Write port to shared config
    PortConfig.write_backend_port(port)
    
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
    
    # Wait for processes to fully terminate with staggered timeouts
    if uvicorn_killed > 0 or node_killed > 0 or python_killed > 0:
        print("- Allowing time for graceful shutdowns and database cleanup...")
        time.sleep(8)  # Longer wait for database connections and services to close
        
        # Verify processes are actually terminated
        print("- Verifying process termination...")
        verify_processes_terminated()
        
        # Additional wait for port release from TIME_WAIT state
        print("- Waiting for port release...")
        time.sleep(2)
    
    # Step 2: Find available port
    print("\nStep 2: Finding available port")
    # Check for command line port argument
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        requested_port = int(sys.argv[1])
        print(f"- Requested port: {requested_port}")
        port = find_free_port(preferred_port=requested_port)
    else:
        # Try to use default port 8000 if available
        port = find_free_port(preferred_port=8000)
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