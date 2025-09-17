# Test API and wait to see console output
import requests
import time

print("Calling expansion API...")
url = "http://localhost:8000/api/events/expand/d77aaa83-2dcf-4097-a6d3-d04f2571d54e"
params = {
    "start_date": "2025-09-15",
    "end_date": "2025-09-18",
    "max_occurrences": 10
}

response = requests.get(url, params=params)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Occurrences: {data['total_occurrences']}")
    
print("\nCheck the backend console for DEBUG output...")
time.sleep(2)