#!/usr/bin/env python3
"""
Quick server restart utility for development
NO EMOJIS
"""

import requests
import sys
import time

def restart_server():
    """Send restart request to the server"""
    try:
        print("Sending restart request to server...")
        response = requests.post("http://localhost:8000/api/restart", timeout=5)
        
        if response.status_code == 200:
            print("Restart initiated successfully")
            print("Server will restart in a moment...")
        else:
            print(f"Restart request failed with status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to server - it might already be down")
    except requests.exceptions.Timeout:
        print("Request timed out - server might be restarting")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    restart_server()