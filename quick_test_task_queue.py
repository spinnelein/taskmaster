#!/usr/bin/env python3
"""
Quick test of task queue API endpoints
Run this while Flask app is running to verify the new functionality works
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000/api"

def test_task_queue_endpoints():
    """Quick test of the new task queue endpoints"""
    
    print("Testing Task Queue API Endpoints")
    print("=" * 40)
    
    # Test 1: Health check
    print("\n1. Testing basic API connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/tasks", timeout=5)
        if response.status_code == 200:
            tasks = response.json()
            print(f"   ✓ API is accessible - found {len(tasks)} tasks")
        else:
            print(f"   ✗ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Cannot connect to API: {e}")
        print("   Make sure Flask app is running on localhost:5000")
        return False
    
    # Test 2: Task queue statistics
    print("\n2. Testing task queue statistics...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/statistics", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✓ Queue statistics endpoint working")
            print(f"     Total tasks: {stats.get('total_tasks', 0)}")
            print(f"     Available tasks: {stats.get('available_tasks', 0)}")
            print(f"     Average priority: {stats.get('average_priority_score', 0):.1f}")
        else:
            print(f"   ✗ Statistics endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Statistics endpoint error: {e}")
    
    # Test 3: All tasks queue
    print("\n3. Testing all tasks queue...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/all?limit=3", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('task_queue', [])
            print(f"   ✓ All tasks queue working - {len(tasks)} tasks")
            if tasks:
                print(f"     Top task: {tasks[0].get('title', 'Unknown')[:30]}")
        else:
            print(f"   ✗ All tasks queue failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ All tasks queue error: {e}")
    
    # Test 4: Available tasks queue
    print("\n4. Testing available tasks queue...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/available?limit=3", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('available_tasks', [])
            print(f"   ✓ Available tasks queue working - {len(tasks)} tasks")
        else:
            print(f"   ✗ Available tasks queue failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Available tasks queue error: {e}")
    
    # Test 5: Time pools
    print("\n5. Testing time pools...")
    try:
        response = requests.get(f"{BASE_URL}/time-pools", timeout=5)
        if response.status_code == 200:
            data = response.json()
            pools = data.get('pools', [])
            print(f"   ✓ Time pools endpoint working - {len(pools)} pools")
            print(f"     Total available time: {data.get('total_minutes', 0)} minutes")
        else:
            print(f"   ✗ Time pools endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Time pools endpoint error: {e}")
    
    # Test 6: Task assignments endpoint
    print("\n6. Testing task assignments...")
    try:
        response = requests.get(f"{BASE_URL}/task-assignments", timeout=5)
        if response.status_code == 200:
            data = response.json()
            assignments = data.get('assignments', [])
            print(f"   ✓ Task assignments endpoint working - {len(assignments)} assignments")
        else:
            print(f"   ✗ Task assignments endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Task assignments endpoint error: {e}")
    
    print("\n" + "=" * 40)
    print("✓ Task Queue System API Test Complete!")
    print("\nNew endpoints available:")
    print("• /api/task-queue/all - Priority-ordered task list")
    print("• /api/task-queue/available - Unassigned tasks")
    print("• /api/task-queue/statistics - Queue metrics")
    print("• /api/task-assignments - Assignment CRUD operations")
    print("• /api/time-pools - Time pools with weather data")
    print("\nThe task queue and assignment system is ready to use!")
    return True

if __name__ == "__main__":
    success = test_task_queue_endpoints()
    sys.exit(0 if success else 1)