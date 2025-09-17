# Test expansion with debug output
import requests

# Test the expansion endpoint
url = "http://localhost:8000/api/events/expand/d77aaa83-2dcf-4097-a6d3-d04f2571d54e"
params = {
    "start_date": "2025-09-15",
    "end_date": "2025-09-18",
    "max_occurrences": 10
}

print("Testing expansion endpoint...")
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"Found {data['total_occurrences']} occurrences")
    
    # Check for exceptions
    for occ in data['occurrences']:
        date = occ['occurrence_date']
        is_exc = occ.get('is_exception', False)
        title = occ['title']
        print(f"  - {date}: {title} (exception: {is_exc})")
else:
    print(f"Error: {response.status_code}")
    print(response.text)