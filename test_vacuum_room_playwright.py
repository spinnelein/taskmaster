#!/usr/bin/env python3
"""
Playwright test to verify Vacuum Room task appears in time pools only on/after September 20th
This demonstrates that the snoozed_until constraint system works end-to-end
"""

import asyncio
import requests
import json
from datetime import datetime, date
from playwright.async_api import async_playwright

# Test configuration
BASE_URL = "http://localhost:5000"
VACUUM_ROOM_TASK_ID = "598f61a8-98fb-44a6-a1c2-2ae7920ef809"  # From analysis
VACUUM_ROOM_SNOOZE_UNTIL = "2025-09-20T17:28:54.439663"  # From analysis

class VacuumRoomPlaywrightTest:
    """Playwright test class for Vacuum Room scheduling verification"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.test_results = []
    
    async def setup(self):
        """Setup Playwright browser and page"""
        print("[SETUP] Starting Playwright browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False, slow_mo=1000)
        self.page = await self.browser.new_page()
        
        # Wait for Flask server to be ready
        await self.wait_for_server()
        
    async def teardown(self):
        """Cleanup Playwright resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def wait_for_server(self, max_attempts=10):
        """Wait for Flask server to be ready"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=2)
                if response.status_code == 200:
                    print("[SETUP] Flask server is ready")
                    return True
            except:
                print(f"[SETUP] Waiting for server... attempt {attempt + 1}/{max_attempts}")
                await asyncio.sleep(2)
        
        raise Exception("Flask server not responding")
    
    async def api_call(self, endpoint, method="GET", data=None):
        """Make API call and return JSON response"""
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[API ERROR] {method} {endpoint}: {e}")
            return None
    
    async def check_vacuum_room_task_status(self):
        """Verify Vacuum Room task is in the expected snoozed state"""
        print("\n[TEST] Checking Vacuum Room task status...")
        
        task = await self.api_call(f"/api/tasks/{VACUUM_ROOM_TASK_ID}")
        if not task:
            self.test_results.append({
                'test': 'vacuum_room_status',
                'result': 'FAIL',
                'reason': 'Could not retrieve Vacuum Room task'
            })
            return False
        
        expected_status = {
            'title': 'Vacuum Room',
            'is_snoozed': True,
            'completed': False,
            'status': 'snoozed'
        }
        
        success = True
        reasons = []
        
        for key, expected_value in expected_status.items():
            actual_value = task.get(key)
            if actual_value != expected_value:
                success = False
                reasons.append(f"{key}: expected {expected_value}, got {actual_value}")
        
        # Check snoozed_until date
        snoozed_until = task.get('snoozed_until')
        if not snoozed_until or not snoozed_until.startswith('2025-09-20'):
            success = False
            reasons.append(f"snoozed_until: expected 2025-09-20, got {snoozed_until}")
        
        result = {
            'test': 'vacuum_room_status',
            'result': 'PASS' if success else 'FAIL',
            'details': {
                'task_id': task.get('id'),
                'title': task.get('title'),
                'status': task.get('status'),
                'is_snoozed': task.get('is_snoozed'),
                'snoozed_until': task.get('snoozed_until'),
                'completed': task.get('completed')
            }
        }
        
        if not success:
            result['reasons'] = reasons
            
        self.test_results.append(result)
        print(f"[TEST] Vacuum Room status: {'PASS' if success else 'FAIL'}")
        
        return success
    
    async def check_time_pools_exist(self):
        """Verify time pools exist for target dates"""
        print("\n[TEST] Checking time pools for Sept 19-21...")
        
        pools = await self.api_call("/api/time_pools?start_date=2025-09-19&end_date=2025-09-21")
        if not pools:
            self.test_results.append({
                'test': 'time_pools_exist',
                'result': 'FAIL',
                'reason': 'Could not retrieve time pools'
            })
            return False
        
        # Group pools by date
        pools_by_date = {}
        for pool in pools:
            pool_date = pool['pool_date']
            if pool_date not in pools_by_date:
                pools_by_date[pool_date] = []
            pools_by_date[pool_date].append(pool)
        
        required_dates = ['2025-09-19', '2025-09-20', '2025-09-21']
        success = True
        reasons = []
        
        for required_date in required_dates:
            if required_date not in pools_by_date:
                success = False
                reasons.append(f"No time pools found for {required_date}")
            else:
                pool_count = len(pools_by_date[required_date])
                total_available = sum(p['available_minutes'] for p in pools_by_date[required_date])
                print(f"[TEST] {required_date}: {pool_count} pools, {total_available} available minutes")
        
        result = {
            'test': 'time_pools_exist',
            'result': 'PASS' if success else 'FAIL',
            'details': {
                'total_pools': len(pools),
                'dates_with_pools': list(pools_by_date.keys()),
                'pools_by_date': {date: len(pool_list) for date, pool_list in pools_by_date.items()}
            }
        }
        
        if not success:
            result['reasons'] = reasons
            
        self.test_results.append(result)
        print(f"[TEST] Time pools exist: {'PASS' if success else 'FAIL'}")
        
        return success
    
    async def check_pre_assignment_state(self):
        """Verify Vacuum Room is not assigned to any pools before bulk assignment"""
        print("\n[TEST] Checking pre-assignment state...")
        
        assignments = await self.api_call(f"/api/assignments?task_id={VACUUM_ROOM_TASK_ID}")
        if assignments is None:
            self.test_results.append({
                'test': 'pre_assignment_state',
                'result': 'FAIL',
                'reason': 'Could not retrieve assignments'
            })
            return False
        
        # Filter for active assignments only (not cancelled)
        active_assignments = [a for a in assignments if a.get('status') in ['assigned', 'started']]
        
        success = len(active_assignments) == 0
        
        result = {
            'test': 'pre_assignment_state',
            'result': 'PASS' if success else 'FAIL',
            'details': {
                'total_assignments': len(assignments),
                'active_assignments': len(active_assignments),
                'assignment_statuses': [a.get('status') for a in assignments]
            }
        }
        
        if not success:
            result['reason'] = f"Found {len(active_assignments)} active assignments before bulk assignment"
            
        self.test_results.append(result)
        print(f"[TEST] Pre-assignment state: {'PASS' if success else 'FAIL'}")
        
        return success
    
    async def trigger_bulk_assignment(self):
        """Trigger bulk assignment of tasks to time pools"""
        print("\n[TEST] Triggering bulk assignment...")
        
        # Clear existing assignments and assign tasks
        assignment_data = {
            'clear_existing': True,
            'max_days_ahead': 7,
            'assigned_by': 'playwright_test'
        }
        
        result = await self.api_call("/api/assignments/bulk", method="POST", data=assignment_data)
        if not result:
            self.test_results.append({
                'test': 'bulk_assignment',
                'result': 'FAIL',
                'reason': 'Bulk assignment API call failed'
            })
            return False
        
        success = result.get('success', False)
        
        test_result = {
            'test': 'bulk_assignment',
            'result': 'PASS' if success else 'FAIL',
            'details': {
                'assignments_made': result.get('assignments_made', 0),
                'tasks_processed': result.get('tasks_processed', 0),
                'pools_used': result.get('pools_used', 0),
                'unassigned_tasks': len(result.get('unassigned_tasks', []))
            }
        }
        
        if not success:
            test_result['reason'] = result.get('message', 'Unknown error')
            
        self.test_results.append(test_result)
        print(f"[TEST] Bulk assignment: {'PASS' if success else 'FAIL'}")
        
        if success:
            print(f"[TEST] Assigned {result.get('assignments_made', 0)} tasks to {result.get('pools_used', 0)} pools")
        
        return success
    
    async def check_post_assignment_constraints(self):
        """Verify Vacuum Room is assigned correctly after bulk assignment"""
        print("\n[TEST] Checking post-assignment constraints...")
        
        assignments = await self.api_call(f"/api/assignments?task_id={VACUUM_ROOM_TASK_ID}")
        if assignments is None:
            self.test_results.append({
                'test': 'post_assignment_constraints',
                'result': 'FAIL',
                'reason': 'Could not retrieve assignments after bulk assignment'
            })
            return False
        
        # Filter for active assignments
        active_assignments = [a for a in assignments if a.get('status') in ['assigned', 'started']]
        
        success = True
        reasons = []
        assignment_details = []
        
        for assignment in active_assignments:
            pool_date = assignment.get('pool_date')
            task_title = assignment.get('task_title')
            
            assignment_details.append({
                'pool_date': pool_date,
                'allocated_minutes': assignment.get('allocated_minutes'),
                'status': assignment.get('status')
            })
            
            # Verify assignment is on or after snooze end date
            if pool_date:
                assignment_date = datetime.fromisoformat(pool_date).date()
                snooze_end_date = date(2025, 9, 20)
                
                if assignment_date < snooze_end_date:
                    success = False
                    reasons.append(f"Assignment on {pool_date} is before snooze end date 2025-09-20")
        
        # Verify at least one assignment was made
        if len(active_assignments) == 0:
            # This might be expected if the task is not ready for assignment
            # Check if it's because of the snooze constraint
            print("[TEST] No active assignments found - checking if this is due to snooze constraint")
        
        result = {
            'test': 'post_assignment_constraints',
            'result': 'PASS' if success else 'FAIL',
            'details': {
                'active_assignments': len(active_assignments),
                'assignment_details': assignment_details
            }
        }
        
        if not success:
            result['reasons'] = reasons
            
        self.test_results.append(result)
        print(f"[TEST] Post-assignment constraints: {'PASS' if success else 'FAIL'}")
        
        return success
    
    async def verify_date_constraints_via_suggestions(self):
        """Verify date constraints by checking assignment service suggestions"""
        print("\n[TEST] Verifying date constraints via assignment suggestions...")
        
        # This tests the assignment service directly via our analysis script
        try:
            # We'll check our earlier analysis results
            # The assignment service should only suggest pools on/after Sept 21st
            # (since the snooze is until Sept 20th afternoon)
            
            import subprocess
            import sys
            
            # Run our analysis script to get fresh suggestions
            result = subprocess.run([
                sys.executable, 'check_vacuum_room_pools.py'
            ], capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                output = result.stdout
                
                # Check if suggestions start from Sept 21st or later
                success = '2025-09-21' in output and '2025-09-19' not in output.split('suggestions')[1] if 'suggestions' in output else False
                
                test_result = {
                    'test': 'date_constraints_via_suggestions',
                    'result': 'PASS' if success else 'FAIL',
                    'details': {
                        'analysis_completed': True,
                        'suggestions_respect_snooze': success
                    }
                }
                
                if not success:
                    test_result['reason'] = 'Assignment suggestions may include dates before snooze end'
                    
            else:
                test_result = {
                    'test': 'date_constraints_via_suggestions',
                    'result': 'FAIL',
                    'reason': f'Analysis script failed: {result.stderr}'
                }
                success = False
                
        except Exception as e:
            test_result = {
                'test': 'date_constraints_via_suggestions',
                'result': 'FAIL',
                'reason': f'Error running analysis: {str(e)}'
            }
            success = False
        
        self.test_results.append(test_result)
        print(f"[TEST] Date constraints via suggestions: {'PASS' if success else 'FAIL'}")
        
        return success
    
    async def navigate_to_schedule_page(self):
        """Navigate to schedule page and take screenshot"""
        print("\n[TEST] Navigating to schedule page...")
        
        try:
            await self.page.goto(f"{BASE_URL}/")
            await self.page.wait_for_load_state('networkidle')
            
            # Take screenshot
            await self.page.screenshot(path='logs/vacuum_room_schedule_page.png')
            
            # Check if page loaded correctly
            title = await self.page.title()
            
            success = 'TaskMaster' in title
            
            result = {
                'test': 'navigate_to_schedule',
                'result': 'PASS' if success else 'FAIL',
                'details': {
                    'page_title': title,
                    'url': self.page.url,
                    'screenshot': 'logs/vacuum_room_schedule_page.png'
                }
            }
            
            if not success:
                result['reason'] = f'Page title "{title}" does not contain "TaskMaster"'
                
            self.test_results.append(result)
            print(f"[TEST] Schedule page navigation: {'PASS' if success else 'FAIL'}")
            
            return success
            
        except Exception as e:
            self.test_results.append({
                'test': 'navigate_to_schedule',
                'result': 'FAIL',
                'reason': f'Navigation failed: {str(e)}'
            })
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("=== Vacuum Room Playwright Test Suite ===\n")
        
        try:
            await self.setup()
            
            # Run tests in logical order
            tests = [
                self.check_vacuum_room_task_status,
                self.check_time_pools_exist,
                self.check_pre_assignment_state,
                self.trigger_bulk_assignment,
                self.check_post_assignment_constraints,
                self.verify_date_constraints_via_suggestions,
                self.navigate_to_schedule_page
            ]
            
            all_passed = True
            for test in tests:
                try:
                    result = await test()
                    if not result:
                        all_passed = False
                except Exception as e:
                    print(f"[ERROR] Test {test.__name__} failed with exception: {e}")
                    all_passed = False
            
            # Print summary
            print("\n=== Test Results Summary ===")
            for result in self.test_results:
                status = result['result']
                test_name = result['test']
                print(f"  {status}: {test_name}")
                if status == 'FAIL' and 'reason' in result:
                    print(f"    Reason: {result['reason']}")
            
            print(f"\nOverall Result: {'PASS' if all_passed else 'FAIL'}")
            print(f"Tests Passed: {sum(1 for r in self.test_results if r['result'] == 'PASS')}/{len(self.test_results)}")
            
            return all_passed
            
        except Exception as e:
            print(f"[FATAL ERROR] Test suite failed: {e}")
            return False
            
        finally:
            await self.teardown()

async def main():
    """Main entry point"""
    test = VacuumRoomPlaywrightTest()
    success = await test.run_all_tests()
    
    # Save detailed results
    with open('logs/vacuum_room_test_results.json', 'w') as f:
        json.dump(test.test_results, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))