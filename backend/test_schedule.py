#!/usr/bin/env python3
"""
Test schedule endpoint specifically
NO EMOJIS
"""
import requests
import json

def test_schedule_endpoint():
    backend_url = "http://localhost:8000"
    
    print("=== TESTING SCHEDULE ENDPOINT ===")
    
    endpoints = [
        "/api/events",
        "/api/events/schedule"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            response = requests.get(f"{backend_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 'N/A')
                events = data.get('events', [])
                
                print(f"  Status: 200 OK")
                print(f"  Total events: {total}")
                
                if events:
                    print(f"  Sample event: {events[0]['title']} at {events[0]['start_time']}")
                
            else:
                print(f"  Status: {response.status_code}")
                print(f"  Error: {response.text}")
            
            print()
                
        except Exception as e:
            print(f"  Error: {e}")
            print()

if __name__ == "__main__":
    test_schedule_endpoint()