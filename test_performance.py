import time
import requests
import json

def time_request(method, url, headers=None, data=None):
    """Time a single request and return response time in milliseconds"""
    start = time.time()
    
    if method == 'POST':
        response = requests.post(url, headers=headers, data=data)
    else:
        response = requests.get(url, headers=headers)
    
    elapsed = (time.time() - start) * 1000  # Convert to milliseconds
    
    return response, elapsed

# Test configuration
base_url = "http://localhost:5000"
json_headers = {"Content-Type": "application/json"}

print("=== TaskMaster Flask API Performance Testing ===\n")

# Test 1: Bulk assignment
print("1. Testing POST /api/assignments/bulk-assign")
response, elapsed = time_request('POST', f"{base_url}/api/assignments/bulk-assign", headers=json_headers, data='{}')
print(f"   Response time: {elapsed:.2f}ms")
print(f"   Status code: {response.status_code}")
print(f"   Response size: {len(response.content)} bytes")

# Test 2: Task queue
print("\n2. Testing GET /api/task-queue/all")
response, elapsed = time_request('GET', f"{base_url}/api/task-queue/all")
print(f"   Response time: {elapsed:.2f}ms")
print(f"   Status code: {response.status_code}")
print(f"   Response size: {len(response.content)} bytes")
data = response.json()
print(f"   Tasks in queue: {data.get('count', 0)}")

# Test 3: Available tasks queue
print("\n3. Testing GET /api/task-queue/available")
response, elapsed = time_request('GET', f"{base_url}/api/task-queue/available")
print(f"   Response time: {elapsed:.2f}ms")
print(f"   Status code: {response.status_code}")
print(f"   Response size: {len(response.content)} bytes")

# Test 4: Time pools
print("\n4. Testing GET /api/time-pools")
response, elapsed = time_request('GET', f"{base_url}/api/time-pools")
print(f"   Response time: {elapsed:.2f}ms")
print(f"   Status code: {response.status_code}")
print(f"   Response size: {len(response.content)} bytes")
data = response.json()
print(f"   Pool count: {data.get('pool_count', 0)}")

# Test 5: Tasks list
print("\n5. Testing GET /api/tasks")
response, elapsed = time_request('GET', f"{base_url}/api/tasks")
print(f"   Response time: {elapsed:.2f}ms")
print(f"   Status code: {response.status_code}")
print(f"   Response size: {len(response.content)} bytes")

# Test 6: Events list
print("\n6. Testing GET /api/events")
response, elapsed = time_request('GET', f"{base_url}/api/events")
print(f"   Response time: {elapsed:.2f}ms")
print(f"   Status code: {response.status_code}")
print(f"   Response size: {len(response.content)} bytes")

# Save performance summary
performance_summary = {
    "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "endpoints_tested": 6,
    "bulk_assign_time_ms": elapsed,
    "all_tests": []
}

# Create docs directory if it doesn't exist
import os
os.makedirs("docs", exist_ok=True)

print("\n=== Performance Testing Complete ===")