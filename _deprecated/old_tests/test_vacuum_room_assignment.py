#!/usr/bin/env python3
"""
Simple test to verify Vacuum Room task assignment respects snoozed_until constraints
This test runs the bulk assignment and verifies the constraint system works
"""

import requests
import json
import sys
from datetime import datetime, date

# Configuration
BASE_URL = "http://localhost:5000"
VACUUM_ROOM_TASK_ID = "598f61a8-98fb-44a6-a1c2-2ae7920ef809"

def check_server():
    """Check if Flask server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Flask server is running")
            return True
    except:
        pass
    
    print("[ERROR] Flask server is not responding")
    print("Please start the Flask server with: cd flask_app && python app.py")
    return False

def get_vacuum_room_task():
    """Get the Vacuum Room task details"""
    try:
        response = requests.get(f"{BASE_URL}/api/tasks/{VACUUM_ROOM_TASK_ID}")
        if response.status_code == 200:
            task = response.json()
            print(f"[TASK] Found: {task['title']}")
            print(f"[TASK] Status: {task['status']}")
            print(f"[TASK] Snoozed: {task.get('is_snoozed', False)}")
            print(f"[TASK] Snoozed Until: {task.get('snoozed_until', 'None')}")
            return task
        else:
            print(f"[ERROR] Could not get task: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Exception getting task: {e}")
        return None

def get_current_assignments():
    """Get current assignments for Vacuum Room task"""
    try:
        response = requests.get(f"{BASE_URL}/api/assignments_api?task_id={VACUUM_ROOM_TASK_ID}")
        if response.status_code == 200:
            assignments = response.json()
            active_assignments = [a for a in assignments if a.get('status') in ['assigned', 'started']]
            
            print(f"[ASSIGN] Total assignments: {len(assignments)}")
            print(f"[ASSIGN] Active assignments: {len(active_assignments)}")
            
            for assignment in active_assignments:
                print(f"[ASSIGN] - {assignment.get('pool_date')} ({assignment.get('status')})")
            
            return assignments
        else:
            print(f"[ERROR] Could not get assignments: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Exception getting assignments: {e}")
        return None

def run_bulk_assignment():
    """Trigger bulk assignment"""
    try:
        assignment_data = {
            'clear_existing': True,
            'max_days_ahead': 7,
            'assigned_by': 'test_assignment'
        }
        
        print("[BULK] Starting bulk assignment...")
        response = requests.post(f"{BASE_URL}/api/assignments/bulk_api", json=assignment_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"[BULK] Success: {result.get('success', False)}")
            print(f"[BULK] Message: {result.get('message', 'No message')}")
            print(f"[BULK] Assignments made: {result.get('assignments_made', 0)}")
            print(f"[BULK] Tasks processed: {result.get('tasks_processed', 0)}")
            print(f"[BULK] Pools used: {result.get('pools_used', 0)}")
            
            # Show unassigned tasks
            unassigned = result.get('unassigned_tasks', [])
            if unassigned:
                print(f"[BULK] Unassigned tasks: {len(unassigned)}")
                for task in unassigned[:5]:  # Show first 5
                    print(f"[BULK]   - {task.get('title', 'Unknown')}")
            
            return result
        else:
            print(f"[ERROR] Bulk assignment failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"[ERROR] Details: {error_data}")
            except:
                print(f"[ERROR] Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Exception in bulk assignment: {e}")
        return None

def verify_constraint_compliance():
    """Verify that assignments respect the snoozed_until constraint"""
    print("\n[VERIFY] Checking constraint compliance...")
    
    assignments = get_current_assignments()
    if not assignments:
        print("[VERIFY] No assignments to check")
        return False
    
    # Filter active assignments
    active_assignments = [a for a in assignments if a.get('status') in ['assigned', 'started']]
    
    if not active_assignments:
        print("[VERIFY] No active assignments found")
        print("[VERIFY] This could be correct if task is still snoozed")
        return True  # Not necessarily a failure
    
    # Check each assignment date
    snooze_end_date = date(2025, 9, 20)  # September 20th
    violations = []
    
    for assignment in active_assignments:
        pool_date_str = assignment.get('pool_date')
        if pool_date_str:
            try:
                pool_date = datetime.fromisoformat(pool_date_str).date()
                if pool_date < snooze_end_date:
                    violations.append(f"Assignment on {pool_date} is before snooze end {snooze_end_date}")
                else:
                    print(f"[VERIFY] OK Assignment on {pool_date} respects constraint")
            except:
                print(f"[VERIFY] Could not parse date: {pool_date_str}")
    
    if violations:
        print("[VERIFY] ❌ CONSTRAINT VIOLATIONS FOUND:")
        for violation in violations:
            print(f"[VERIFY]   - {violation}")
        return False
    else:
        print("[VERIFY] [OK] All assignments respect snoozed_until constraint")
        return True

def main():
    """Main test execution"""
    print("=== Vacuum Room Assignment Constraint Test ===\n")
    
    # Step 1: Check server
    if not check_server():
        return 1
    
    # Step 2: Get task details
    print("\n--- Task Details ---")
    task = get_vacuum_room_task()
    if not task:
        return 1
    
    # Step 3: Check current assignments (before)
    print("\n--- Pre-Assignment State ---")
    pre_assignments = get_current_assignments()
    
    # Step 4: Run bulk assignment
    print("\n--- Bulk Assignment ---")
    bulk_result = run_bulk_assignment()
    if not bulk_result:
        return 1
    
    # Step 5: Check assignments after
    print("\n--- Post-Assignment State ---")
    post_assignments = get_current_assignments()
    
    # Step 6: Verify constraint compliance
    constraint_ok = verify_constraint_compliance()
    
    # Summary
    print("\n=== TEST SUMMARY ===")
    print(f"Task found: [OK]")
    print(f"Bulk assignment ran: [OK]")
    print(f"Constraint compliance: {'[OK]' if constraint_ok else '[FAIL]'}")
    
    if constraint_ok:
        print("\n[PASS] TEST PASSED: Vacuum Room task assignment respects snoozed_until constraint")
        return 0
    else:
        print("\n[FAIL] TEST FAILED: Constraint violations detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())