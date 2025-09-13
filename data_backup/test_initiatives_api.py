#!/usr/bin/env python3
"""
Test initiatives API with fresh database
NO EMOJIS
"""
import requests
import json
import time

def test_api_endpoint(url, method='GET', data=None, max_time=10):
    """Test an API endpoint with timeout"""
    try:
        print(f"Testing {method} {url}...")
        
        if method == 'GET':
            response = requests.get(url, timeout=max_time)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=max_time, 
                                   headers={'Content-Type': 'application/json'})
        else:
            print(f"Unsupported method: {method}")
            return False
        
        print(f"Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:200]}...")
        else:
            print(f"Response: {response.text[:200]}...")
        
        return response.status_code < 400
        
    except requests.exceptions.Timeout:
        print(f"TIMEOUT: Request took longer than {max_time} seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Test initiatives API"""
    print("Testing Initiatives API")
    print("=" * 30)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint first
    if not test_api_endpoint(f"{base_url}/health"):
        print("Server is not responding. Make sure it's running with the new database.")
        return
    
    print("\nTesting initiatives endpoints...")
    
    # Test GET initiatives (should be empty)
    print("\n1. Testing GET /api/initiatives")
    if test_api_endpoint(f"{base_url}/api/initiatives"):
        print("✓ GET initiatives works")
    else:
        print("✗ GET initiatives failed")
        return
    
    # Test POST initiatives (create new)
    print("\n2. Testing POST /api/initiatives")
    test_initiative = {
        "title": "API Test Initiative",
        "description": "Testing the initiatives API functionality",
        "frequency": "weekly",
        "interval": 1
    }
    
    if test_api_endpoint(f"{base_url}/api/initiatives", method='POST', data=test_initiative):
        print("✓ POST initiatives works")
    else:
        print("✗ POST initiatives failed")
        return
    
    # Test GET again to see the created initiative
    print("\n3. Testing GET /api/initiatives (should show created initiative)")
    if test_api_endpoint(f"{base_url}/api/initiatives"):
        print("✓ GET initiatives with data works")
    else:
        print("✗ GET initiatives with data failed")
    
    print("\nAll API tests completed!")

if __name__ == "__main__":
    main()