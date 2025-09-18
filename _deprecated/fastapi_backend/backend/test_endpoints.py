#!/usr/bin/env python3
"""
Test simple API endpoint to debug SQLAlchemy issues
NO EMOJIS
"""
import requests
import json

def test_endpoints():
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/health",
        "/api/events",
        "/api/tasks", 
        "/api/initiatives",
        "/api/projects"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}")
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'total' in data:
                    print(f"  Total: {data['total']}")
                else:
                    print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"  Error: {response.text}")
            print()
                
        except Exception as e:
            print(f"  Exception: {e}")
            print()

if __name__ == "__main__":
    test_endpoints()