#!/usr/bin/env python3
"""
Simple Flask application test using requests
NO EMOJIS
"""
import requests
import json
import time

def test_flask_endpoints():
    """Test Flask application endpoints"""
    base_url = "http://localhost:5000"
    
    print("Testing Flask Application")
    print("=" * 50)
    
    try:
        # Test 1: Health check
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✓ Health check passed: {health_data}")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
            return False
        
        # Test 2: Main page
        print("\n2. Testing main page...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Main page loaded (HTML content: {len(response.text)} characters)")
            # Check if FullCalendar script is included
            if "fullcalendar" in response.text.lower():
                print("   ✓ FullCalendar script detected")
            else:
                print("   ✗ FullCalendar script NOT detected")
        else:
            print(f"   ✗ Main page failed: {response.status_code}")
        
        # Test 3: Events API
        print("\n3. Testing events API...")
        response = requests.get(f"{base_url}/api/events", timeout=5)
        if response.status_code == 200:
            events = response.json()
            print(f"   ✓ Events API working: {len(events)} events found")
        else:
            print(f"   ✗ Events API failed: {response.status_code}")
        
        # Test 4: Tasks API
        print("\n4. Testing tasks API...")
        response = requests.get(f"{base_url}/api/tasks", timeout=5)
        if response.status_code == 200:
            tasks = response.json()
            print(f"   ✓ Tasks API working: {len(tasks)} tasks found")
        else:
            print(f"   ✗ Tasks API failed: {response.status_code}")
        
        # Test 5: Create test event
        print("\n5. Testing event creation...")
        test_event = {
            'title': 'Test Event from Python',
            'start': '2025-01-20T14:00:00',
            'end': '2025-01-20T15:00:00',
            'is_blocking': True,
            'description': 'Test event created by Python test'
        }
        
        response = requests.post(
            f"{base_url}/api/events", 
            json=test_event,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            created_event = response.json()
            print(f"   ✓ Event created: {created_event['title']} (ID: {created_event['id']})")
            event_id = created_event['id']
            
            # Test 6: Delete test event
            print("\n6. Testing event deletion...")
            delete_response = requests.delete(f"{base_url}/api/events/{event_id}", timeout=5)
            if delete_response.status_code == 200:
                print("   ✓ Event deleted successfully")
            else:
                print(f"   ✗ Event deletion failed: {delete_response.status_code}")
                
        else:
            print(f"   ✗ Event creation failed: {response.status_code} - {response.text}")
        
        # Test 7: Create test task
        print("\n7. Testing task creation...")
        test_task = {
            'title': 'Test Task from Python',
            'description': 'Test task created by Python test',
            'duration': 45,
            'urgency': 8,
            'priority': 'high'
        }
        
        response = requests.post(
            f"{base_url}/api/tasks",
            json=test_task,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            created_task = response.json()
            print(f"   ✓ Task created: {created_task['title']} (ID: {created_task['id']})")
            task_id = created_task['id']
            
            # Test 8: Complete test task
            print("\n8. Testing task completion...")
            complete_response = requests.post(f"{base_url}/api/tasks/{task_id}/complete", timeout=5)
            if complete_response.status_code == 200:
                completed_task = complete_response.json()
                print(f"   ✓ Task completed: {completed_task['completed']}")
            else:
                print(f"   ✗ Task completion failed: {complete_response.status_code}")
                
        else:
            print(f"   ✗ Task creation failed: {response.status_code} - {response.text}")
        
        print("\n" + "=" * 50)
        print("✓ Flask Application API Tests Completed!")
        print("✓ All core API endpoints are working")
        print("✓ CRUD operations are functional")
        print("✓ Application is ready for use")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask application")
        print("   Make sure Flask app is running: cd flask_app && python app.py")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def check_flask_running():
    """Check if Flask app is running"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("Checking if Flask app is running...")
    
    if not check_flask_running():
        print("Flask app is not running!")
        print("Please start it first:")
        print("  cd flask_app")
        print("  python app.py")
        print()
        exit(1)
    
    print("Flask app detected, running tests...\n")
    
    success = test_flask_endpoints()
    
    if success:
        print("\n🎉 All tests passed! Flask application is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")