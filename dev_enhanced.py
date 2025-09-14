#!/usr/bin/env python3
"""
TaskMaster Enhanced Development Environment Manager
NO EMOJIS

Usage:
    python dev_enhanced.py          # Start both backend and frontend
    python dev_enhanced.py backend  # Start only backend
    python dev_enhanced.py frontend # Start only frontend  
    python dev_enhanced.py stop     # Stop all services
    python dev_enhanced.py status   # Show service status
    python dev_enhanced.py clean    # Clean up all processes and ports
"""

import os
import sys
import time
import subprocess
import psutil
import socket
import json
import re
import threading
from pathlib import Path
import signal
import atexit

# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
FRONTEND_PORT_RANGE = range(5173, 5180)  # Ports Vite will try
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
PID_FILE = PROJECT_ROOT / ".taskmaster_pids.json"

# Colors for output (disable on Windows for now)
class Colors:
    if os.name == 'nt':  # Windows
        HEADER = ''
        BLUE = ''
        GREEN = ''
        YELLOW = ''
        RED = ''
        END = ''
        BOLD = ''
    else:
        HEADER = '\033[95m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        END = '\033[0m'
        BOLD = '\033[1m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}[OK] {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}[INFO] {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.END}")

def load_pids():
    """Load saved PIDs from file"""
    if PID_FILE.exists():
        try:
            with open(PID_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pids(pids):
    """Save PIDs to file"""
    with open(PID_FILE, 'w') as f:
        json.dump(pids, f)

def cleanup_pids():
    """Remove PID file on exit"""
    if PID_FILE.exists():
        PID_FILE.unlink()

def is_port_available(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('localhost', port))
            return True
    except (OSError, socket.timeout):
        return False

def find_process_using_port(port):
    """Find process using a specific port"""
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == port and conn.status == 'LISTEN':
            try:
                process = psutil.Process(conn.pid)
                return {'pid': conn.pid, 'name': process.name(), 'cmdline': ' '.join(process.cmdline())}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return {'pid': conn.pid, 'name': 'Unknown', 'cmdline': 'Access Denied'}
    return None

def kill_port_process(port):
    """Kill process using a specific port"""
    process_info = find_process_using_port(port)
    if process_info:
        print_info(f"Found process on port {port}: {process_info['name']} (PID: {process_info['pid']})")
        try:
            process = psutil.Process(process_info['pid'])
            process.terminate()
            try:
                process.wait(timeout=5)
                print_success(f"Killed process on port {port}")
                return True
            except psutil.TimeoutExpired:
                process.kill()
                print_success(f"Force killed process on port {port}")
                return True
        except Exception as e:
            print_error(f"Failed to kill process on port {port}: {e}")
            return False
    return True

def clean_all_ports():
    """Clean all TaskMaster related ports"""
    print_info("Cleaning up ports...")
    
    # Clean backend port
    if not is_port_available(BACKEND_PORT):
        kill_port_process(BACKEND_PORT)
    
    # Clean frontend ports
    for port in FRONTEND_PORT_RANGE:
        if not is_port_available(port):
            process_info = find_process_using_port(port)
            if process_info and 'vite' in process_info.get('cmdline', '').lower():
                kill_port_process(port)
    
    # Kill any orphaned node processes running vite
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline_list = proc.info.get('cmdline', None)
            if cmdline_list and isinstance(cmdline_list, list):
                cmdline = ' '.join(cmdline_list)
                if 'vite' in cmdline and str(FRONTEND_DIR) in cmdline:
                    print_info(f"Found orphaned Vite process (PID: {proc.info['pid']})")
                    proc.terminate()
                    proc.wait(timeout=3)
                    print_success(f"Killed orphaned Vite process")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired, TypeError):
            pass

def wait_for_port(port, timeout=30):
    """Wait for a port to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_available(port):
            return True
        time.sleep(1)
    return False

def is_process_running(pid):
    """Check if a process with given PID is running"""
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def stop_process(pid, name="Process"):
    """Stop a process gracefully, then forcefully if needed"""
    try:
        process = psutil.Process(pid)
        print_info(f"Stopping {name} (PID: {pid})...")
        
        # Try graceful termination first
        process.terminate()
        try:
            process.wait(timeout=5)
            print_success(f"{name} stopped gracefully")
        except psutil.TimeoutExpired:
            # Force kill if graceful shutdown failed
            print_warning(f"{name} didn't stop gracefully, forcing...")
            process.kill()
            process.wait(timeout=3)
            print_success(f"{name} stopped forcefully")
            
    except psutil.NoSuchProcess:
        print_info(f"{name} already stopped")
    except Exception as e:
        print_error(f"Error stopping {name}: {e}")

def start_backend():
    """Start the backend server"""
    print_info("Starting backend server...")
    
    # Check if already running
    pids = load_pids()
    if 'backend' in pids and is_process_running(pids['backend']):
        print_warning(f"Backend already running on port {BACKEND_PORT}")
        return pids['backend']
    
    # Check port availability
    if not is_port_available(BACKEND_PORT):
        print_warning(f"Port {BACKEND_PORT} is in use, attempting to clean...")
        if not kill_port_process(BACKEND_PORT):
            print_error(f"Failed to free port {BACKEND_PORT}")
            return None
        time.sleep(2)
    
    # Start backend
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "src.api.app:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", str(BACKEND_PORT)
    ]
    
    process = subprocess.Popen(
        cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Save PID
    pids = load_pids()
    pids['backend'] = process.pid
    save_pids(pids)
    
    # Wait for server to start
    print_info(f"Waiting for backend to start on port {BACKEND_PORT}...")
    time.sleep(3)
    
    # Verify it's running
    if process.poll() is None:
        print_success(f"Backend started on http://localhost:{BACKEND_PORT}")
        print_info(f"API docs: http://localhost:{BACKEND_PORT}/docs")
        return process.pid
    else:
        print_error("Backend failed to start")
        return None

def parse_vite_output(process):
    """Parse Vite output to find actual port"""
    actual_port = None
    port_pattern = re.compile(r'Local:\s+http://localhost:(\d+)')
    
    def read_output():
        nonlocal actual_port
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"  {Colors.BLUE}[Vite]{Colors.END} {line.strip()}")
                match = port_pattern.search(line)
                if match:
                    actual_port = int(match.group(1))
    
    # Start thread to read output
    thread = threading.Thread(target=read_output)
    thread.daemon = True
    thread.start()
    
    # Wait for port detection
    timeout = 15
    start_time = time.time()
    while actual_port is None and time.time() - start_time < timeout:
        if process.poll() is not None:
            print_error("Vite process terminated unexpectedly")
            break
        time.sleep(0.5)
    
    return actual_port

def start_frontend():
    """Start the frontend server with port detection"""
    print_info("Starting frontend server...")
    
    # Check if already running
    pids = load_pids()
    if 'frontend' in pids and is_process_running(pids['frontend']):
        frontend_port = pids.get('frontend_port', FRONTEND_PORT)
        print_warning(f"Frontend already running on port {frontend_port}")
        return pids['frontend']
    
    # Clean all potential frontend ports
    for port in FRONTEND_PORT_RANGE:
        if not is_port_available(port):
            process_info = find_process_using_port(port)
            if process_info and 'vite' in process_info.get('cmdline', '').lower():
                print_info(f"Cleaning up Vite process on port {port}")
                kill_port_process(port)
    
    time.sleep(2)  # Give OS time to release ports
    
    # Set environment variable for backend URL
    env = os.environ.copy()
    env['VITE_API_URL'] = f'http://localhost:{BACKEND_PORT}/api'
    
    # Start frontend (let Vite choose the port)
    if os.name == 'nt':  # Windows
        cmd = ["npm.cmd", "run", "dev"]
    else:  # Unix/Linux/Mac
        cmd = ["npm", "run", "dev"]
    
    process = subprocess.Popen(
        cmd,
        cwd=FRONTEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    print_info("Waiting for Vite to start...")
    
    # Parse output to find actual port
    actual_port = parse_vite_output(process)
    
    if actual_port and process.poll() is None:
        # Save PID and actual port
        pids = load_pids()
        pids['frontend'] = process.pid
        pids['frontend_port'] = actual_port
        save_pids(pids)
        
        print_success(f"Frontend started on http://localhost:{actual_port}")
        if actual_port != FRONTEND_PORT:
            print_warning(f"Note: Using port {actual_port} instead of default {FRONTEND_PORT}")
        
        return process.pid
    else:
        print_error("Frontend failed to start or port not detected")
        if process.poll() is None:
            process.terminate()
        return None

def stop_all():
    """Stop all services"""
    print_header("Stopping TaskMaster Services")
    
    pids = load_pids()
    
    # Stop frontend first
    if 'frontend' in pids:
        stop_process(pids['frontend'], "Frontend")
    
    # Stop backend
    if 'backend' in pids:
        stop_process(pids['backend'], "Backend")
    
    # Clean up PID file
    cleanup_pids()
    
    print_success("All services stopped")

def show_status():
    """Show status of all services"""
    print_header("TaskMaster Service Status")
    
    pids = load_pids()
    
    # Check backend
    if 'backend' in pids and is_process_running(pids['backend']):
        print_success(f"Backend: Running (PID: {pids['backend']}, Port: {BACKEND_PORT})")
        print_info(f"  URL: http://localhost:{BACKEND_PORT}")
        print_info(f"  API Docs: http://localhost:{BACKEND_PORT}/docs")
    else:
        print_error("Backend: Not running")
    
    # Check frontend
    if 'frontend' in pids and is_process_running(pids['frontend']):
        frontend_port = pids.get('frontend_port', FRONTEND_PORT)
        print_success(f"Frontend: Running (PID: {pids['frontend']}, Port: {frontend_port})")
        print_info(f"  URL: http://localhost:{frontend_port}")
    else:
        print_error("Frontend: Not running")
    
    # Check port availability
    print_info("\nPort Status:")
    if not is_port_available(BACKEND_PORT):
        process_info = find_process_using_port(BACKEND_PORT)
        if process_info:
            print_warning(f"  Port {BACKEND_PORT}: In use by {process_info['name']} (PID: {process_info['pid']})")
        else:
            print_warning(f"  Port {BACKEND_PORT}: In use")
    else:
        print_info(f"  Port {BACKEND_PORT}: Available")
    
    # Check all potential frontend ports
    for port in FRONTEND_PORT_RANGE:
        if not is_port_available(port):
            process_info = find_process_using_port(port)
            if process_info:
                print_warning(f"  Port {port}: In use by {process_info['name']} (PID: {process_info['pid']})")

def main():
    """Main entry point"""
    # Register cleanup on exit
    atexit.register(cleanup_pids)
    
    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if command in ["all", ""]:
        print_header("Starting TaskMaster Development Environment")
        
        # Clean ports first
        clean_all_ports()
        
        # Start backend first
        backend_pid = start_backend()
        if not backend_pid:
            print_error("Failed to start backend, aborting")
            sys.exit(1)
        
        # Give backend time to fully initialize
        time.sleep(2)
        
        # Start frontend
        frontend_pid = start_frontend()
        if not frontend_pid:
            print_error("Failed to start frontend")
            # Don't exit, backend is still running
        
        print_header("TaskMaster Development Environment Ready")
        pids = load_pids()
        print_info(f"Backend: http://localhost:{BACKEND_PORT}")
        print_info(f"Frontend: http://localhost:{pids.get('frontend_port', FRONTEND_PORT)}")
        print_info("Press Ctrl+C to stop all services")
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n")
            stop_all()
            
    elif command == "backend":
        print_header("Starting Backend Only")
        clean_all_ports()
        start_backend()
        
    elif command == "frontend":
        print_header("Starting Frontend Only")
        clean_all_ports()
        start_frontend()
        
    elif command == "stop":
        stop_all()
        
    elif command == "status":
        show_status()
        
    elif command == "clean":
        print_header("Cleaning All Ports and Processes")
        clean_all_ports()
        cleanup_pids()
        print_success("Cleanup complete")
        
    else:
        print_error(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()