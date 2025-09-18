#!/usr/bin/env python3
"""
Simple API test for port 8001
NO EMOJIS
"""
import requests
import json

def test_initiatives_api():
    """Test initiatives API on new database"""
    base_url = "http://localhost:8001"
    
    print("Testing server health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    print("\nTesting GET /api/initiatives...")
    try:
        response = requests.get(f"{base_url}/api/initiatives", timeout=10)
        print(f"GET initiatives: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"GET initiatives failed: {e}")
        return
    
    print("\nTesting POST /api/initiatives...")
    test_data = {
        "title": "Database Test Initiative",
        "description": "Testing with fresh database",
        "frequency": "daily",
        "interval": 1
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/initiatives", 
            json=test_data, 
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        print(f"POST initiatives: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"Created: {json.dumps(data, indent=2)}")
            return data.get('id')
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"POST initiatives failed: {e}")
    
    return None

if __name__ == "__main__":
    test_initiatives_api()