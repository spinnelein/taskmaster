import sys
import os
import time
import psutil
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), "flask_app"))

print("Testing Performance & Resource Usage:")
start_overall = time.time()

# Test 1: Startup performance
print("\n1. Startup Performance:")
start_time = time.time()
from app import create_app
app = create_app()
startup_time = time.time() - start_time
print(f"   Flask startup time: {startup_time:.3f} seconds")
startup_ok = startup_time < 5.0
print(f"   Startup performance: {\"PASS\" if startup_ok else \"FAIL\"}")

# Test 2: Memory usage
print("\n2. Memory Usage:")
process = psutil.Process()
memory_info = process.memory_info()
memory_mb = memory_info.rss / 1024 / 1024
print(f"   Memory RSS: {memory_mb:.1f} MB")
memory_ok = memory_mb < 200
print(f"   Memory usage: {\"PASS\" if memory_ok else \"FAIL\"}")

# Test 3: API response times
print("\n3. API Response Times:")
with app.test_client() as client:
    endpoints = ["/api/tasks", "/api/events", "/api/initiatives"]
    times = []
    for endpoint in endpoints:
        start_time = time.time()
        response = client.get(endpoint)
        response_time = time.time() - start_time
        times.append(response_time)
        print(f"   {endpoint}: {response_time:.3f}s ({response.status_code})")
    
    avg_time = sum(times) / len(times)
    response_ok = avg_time < 1.0
    print(f"   Average: {avg_time:.3f}s - {\"PASS\" if response_ok else \"FAIL\"}")

# Summary
results = [startup_ok, memory_ok, response_ok]
passed = sum(results)
total = len(results)
overall_time = time.time() - start_overall

print(f"\nPERFORMANCE SUMMARY: {passed}/{total} tests passed")
print(f"Total test time: {overall_time:.3f} seconds")
print(f"INTEGRATION TEST 6: {\"PASSED\" if passed >= 2 else \"FAILED\"} - Performance")

