#!/usr/bin/env python3
"""Test script to verify tasks show up in time pools on schedule"""

import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:5000"

def test_schedule_display():
    print("Testing Task Display in Time Pools on Schedule")
    print("=" * 50)
    
    # 1. Check current assignments
    print("\n1. Current Task Assignments in Time Pools:")
    response = requests.get(f"{BASE_URL}/api/time-pools?limit=7&include_weather=true")
    
    if response.status_code == 200:
        data = response.json()
        pools_with_tasks = 0
        total_tasks_assigned = 0
        
        for pool in data.get('pools', []):
            assignments = pool.get('assignments', [])
            if assignments:
                pools_with_tasks += 1
                pool_date = pool.get('pool_date', 'Unknown')
                print(f"\n   Pool: {pool_date}")
                print(f"   Allocated: {pool.get('allocated_minutes', 0)}/{pool.get('total_minutes', 0)} minutes")
                print("   Tasks:")
                for assignment in assignments:
                    total_tasks_assigned += 1
                    print(f"   - {assignment.get('task_title', 'Unknown')} ({assignment.get('allocated_minutes', 0)} min)")
        
        print(f"\n   Summary: {pools_with_tasks} pools have tasks, {total_tasks_assigned} total assignments")
    else:
        print(f"   [FAIL] Could not fetch time pools: {response.status_code}")
    
    # 2. Instructions for visual verification
    print("\n2. Visual Verification Instructions:")
    print("   a) Open http://localhost:5000/schedule in your browser")
    print("   b) Look for time pools (green/yellow/red blocks)")
    print("   c) Under each pool title, you should see assigned tasks listed")
    print("   d) Example:")
    print("      Time Pool (20/480m)")
    print("      Dishes (20m)")
    print("\n3. Expected Results:")
    print("   - Time pools should show as colored blocks on the calendar")
    print("   - Each pool should display allocated/total minutes")
    print("   - Assigned tasks should appear below the pool title")
    print("   - Task format: '• Task Name (Xm)' or just 'Task Name (Xm)'")
    
    print("\n" + "=" * 50)
    print("Schedule URL: http://localhost:5000/schedule")

if __name__ == "__main__":
    test_schedule_display()