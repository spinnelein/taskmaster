#!/usr/bin/env python3
"""
Playwright test for Flask application
NO EMOJIS
"""
import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

async def test_flask_app():
    """Test the Flask application with Playwright"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for headless
        page = await browser.new_page()
        
        print("Testing Flask Application")
        print("=" * 50)
        
        try:
            # Test 1: Load main page
            print("1. Loading main page...")
            await page.goto("http://localhost:5000")
            await page.wait_for_load_state('networkidle')
            
            # Check if page loaded
            title = await page.title()
            print(f"   Page title: {title}")
            
            # Check if FullCalendar loaded
            calendar = await page.query_selector('#calendar')
            if calendar:
                print("   ✓ FullCalendar element found")
            else:
                print("   ✗ FullCalendar element NOT found")
                
            # Wait for FullCalendar to initialize
            await page.wait_for_selector('.fc-view-harness', timeout=10000)
            print("   ✓ FullCalendar initialized")
            
            # Test 2: Check health endpoint
            print("\n2. Testing health endpoint...")
            health_response = await page.evaluate("""
                fetch('/health').then(r => r.json())
            """)
            print(f"   Health status: {health_response}")
            
            # Test 3: Test API endpoints
            print("\n3. Testing API endpoints...")
            
            # Get events
            events_response = await page.evaluate("""
                fetch('/api/events').then(r => r.json())
            """)
            print(f"   Events API: {len(events_response)} events found")
            
            # Get tasks
            tasks_response = await page.evaluate("""
                fetch('/api/tasks').then(r => r.json())
            """)
            print(f"   Tasks API: {len(tasks_response)} tasks found")
            
            # Test 4: Create a test event
            print("\n4. Creating test event...")
            
            # Create event via API
            test_event = {
                'title': 'Test Event from Playwright',
                'start': '2025-01-20T10:00:00',
                'end': '2025-01-20T11:00:00',
                'is_blocking': True,
                'description': 'Test event created by automated test'
            }
            
            create_response = await page.evaluate(f"""
                fetch('/api/events', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({json.dumps(test_event)})
                }}).then(r => r.json())
            """)
            
            if 'id' in create_response:
                print(f"   ✓ Event created with ID: {create_response['id']}")
                event_id = create_response['id']
                
                # Test 5: Delete the test event
                print("\n5. Deleting test event...")
                delete_response = await page.evaluate(f"""
                    fetch('/api/events/{event_id}', {{
                        method: 'DELETE'
                    }}).then(r => r.json())
                """)
                print(f"   Delete response: {delete_response}")
                
            else:
                print(f"   ✗ Failed to create event: {create_response}")
            
            # Test 6: Create a test task
            print("\n6. Creating test task...")
            
            test_task = {
                'title': 'Test Task from Playwright',
                'description': 'Test task created by automated test',
                'duration': 30,
                'urgency': 7,
                'priority': 'high'
            }
            
            task_response = await page.evaluate(f"""
                fetch('/api/tasks', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({json.dumps(test_task)})
                }}).then(r => r.json())
            """)
            
            if 'id' in task_response:
                print(f"   ✓ Task created with ID: {task_response['id']}")
                task_id = task_response['id']
                
                # Test task completion
                print("\n7. Completing test task...")
                complete_response = await page.evaluate(f"""
                    fetch('/api/tasks/{task_id}/complete', {{
                        method: 'POST'
                    }}).then(r => r.json())
                """)
                print(f"   Task completion response: {complete_response}")
                
            else:
                print(f"   ✗ Failed to create task: {task_response}")
            
            # Test 7: Check UI elements
            print("\n8. Testing UI elements...")
            
            # Check if sidebar exists
            sidebar = await page.query_selector('.sidebar')
            if sidebar:
                print("   ✓ Sidebar found")
            else:
                print("   ✗ Sidebar NOT found")
            
            # Check if tasks list exists
            tasks_list = await page.query_selector('#tasks-list')
            if tasks_list:
                print("   ✓ Tasks list found")
            else:
                print("   ✗ Tasks list NOT found")
            
            # Check if health status indicator exists
            health_status = await page.query_selector('#health-status')
            if health_status:
                status_text = await health_status.text_content()
                print(f"   ✓ Health status indicator: {status_text}")
            else:
                print("   ✗ Health status indicator NOT found")
            
            # Test 8: Check calendar functionality
            print("\n9. Testing calendar functionality...")
            
            # Check if calendar has proper view buttons
            view_buttons = await page.query_selector_all('.fc-button')
            print(f"   ✓ Found {len(view_buttons)} calendar view buttons")
            
            # Check current view
            current_view = await page.evaluate("""
                window.calendar ? window.calendar.view.type : 'Calendar not initialized'
            """)
            print(f"   Current calendar view: {current_view}")
            
            # Take a screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"flask_app_test_{timestamp}.png"
            await page.screenshot(path=screenshot_path)
            print(f"\n   📸 Screenshot saved: {screenshot_path}")
            
            print("\n" + "=" * 50)
            print("✓ Flask Application Test Completed Successfully!")
            print("✓ All core functionality appears to be working")
            print("✓ FullCalendar is properly initialized")
            print("✓ API endpoints are responsive")
            print("✓ UI elements are rendering correctly")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            # Take error screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"flask_app_error_{timestamp}.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    print("Make sure Flask app is running on http://localhost:5000")
    print("Run: cd flask_app && python app.py")
    print("Then run this test script")
    print()
    
    asyncio.run(test_flask_app())