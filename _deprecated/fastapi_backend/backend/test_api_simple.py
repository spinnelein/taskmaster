#!/usr/bin/env python3
"""
Simple API test for the new recurring events system
"""
import requests
import json
from datetime import date, timedelta

def test_events_api():
    print("Testing Events API")
    print("=" * 30)
    
    try:
        # Test basic events endpoint
        response = requests.get('http://localhost:8000/api/events', timeout=10)
        print(f"Events API status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            total = data.get('total', 0)
            
            print(f"Total events returned: {total}")
            print(f"Events in response: {len(events)}")
            
            # Find recurring events
            recurring_events = [e for e in events if e.get('is_recurring', False)]
            print(f"Recurring events: {len(recurring_events)}")
            
            if recurring_events:
                # Test first recurring event
                event = recurring_events[0]
                event_id = event['id']
                title = event['title']
                
                print(f"\nTesting occurrences for: {title}")
                print(f"Event ID: {event_id}")
                
                # Test occurrences endpoint
                start_date = date.today()
                end_date = start_date + timedelta(days=7)
                
                occ_url = f'http://localhost:8000/api/events/{event_id}/occurrences'
                params = {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'max_occurrences': 10
                }
                
                print(f"Calling: {occ_url}")
                print(f"Params: {params}")
                
                occ_response = requests.get(occ_url, params=params, timeout=10)
                print(f"Occurrences status: {occ_response.status_code}")
                
                if occ_response.status_code == 200:
                    occ_data = occ_response.json()
                    total_occ = occ_data.get('total_occurrences', 0)
                    occurrences = occ_data.get('occurrences', [])
                    
                    print(f"✓ SUCCESS: Generated {total_occ} occurrences")
                    
                    # Show first few occurrences
                    for i, occ in enumerate(occurrences[:3]):
                        occ_date = occ.get('occurrence_date', 'N/A')
                        occ_title = occ.get('title', 'N/A')
                        print(f"  {i+1}. {occ_date} - {occ_title}")
                    
                    return True
                else:
                    print(f"✗ ERROR: {occ_response.status_code}")
                    print(f"Response: {occ_response.text}")
                    return False
            else:
                print("No recurring events found to test")
                return False
        else:
            print(f"✗ ERROR: Events API failed with {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_events_api()
    if success:
        print("\n🎉 API TEST SUCCESSFUL!")
        print("Runtime expansion is working!")
    else:
        print("\n❌ API TEST FAILED")
        print("Need to debug issues...")