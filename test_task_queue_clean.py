#!/usr/bin/env python3
"""
Test script for the complete task queue and assignment system
Tests all the new functionality: priority queues, assignments, matching, etc.
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:5000/api"

def test_task_queue_system():
    """Test the complete task queue and assignment system"""
    
    print("Testing Task Queue and Assignment System")
    print("=" * 60)
    
    # Test 1: Get task queue statistics
    print("\n1. Getting task queue statistics...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/statistics")
        if response.status_code == 200:
            stats = response.json()
            print("   [OK] Queue Statistics:")
            print(f"      Total tasks: {stats.get('total_tasks', 0)}")
            print(f"      Available tasks: {stats.get('available_tasks', 0)}")
            print(f"      Blocked tasks: {stats.get('blocked_tasks', 0)}")
            print(f"      Overdue tasks: {stats.get('overdue_tasks', 0)}")
            print(f"      Snoozed tasks: {stats.get('snoozed_tasks', 0)}")
            print(f"      Average priority: {stats.get('average_priority_score', 0)}")
            print(f"      Assigned tasks: {stats.get('assigned_tasks', 0)}")
        else:
            print(f"   [FAIL] Failed to get statistics: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Statistics error: {e}")
    
    # Test 2: Get all tasks queue
    print("\n2. Getting all tasks queue (top 5)...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/all?limit=5")
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('task_queue', [])
            
            print(f"   [OK] Found {len(tasks)} tasks in queue")
            for i, task in enumerate(tasks[:3]):
                score = task.get('priority_score', 0)
                title = task.get('title', 'Unknown')
                status = task.get('status', 'Unknown')
                due = task.get('due_date', 'No due date')
                
                print(f"      {i+1}. [{score:.1f}] {title}")
                print(f"         Status: {status}, Due: {due}")
                
                if task.get('is_overdue'):
                    print(f"         OVERDUE by {task.get('days_overdue', 0)} days")
                if task.get('is_assigned'):
                    print(f"         Assigned: {task.get('assigned_minutes', 0)}/{task.get('duration', 0)} min")
        else:
            print(f"   [FAIL] Failed to get tasks: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Task queue error: {e}")
    
    # Test 3: Get available tasks queue  
    print("\n3. Getting available tasks queue...")
    available_task_id = None
    try:
        response = requests.get(f"{BASE_URL}/task-queue/available?limit=3")
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('available_tasks', [])
            
            print(f"   [OK] Found {len(tasks)} available tasks")
            if tasks:
                available_task_id = tasks[0]['id']
                for i, task in enumerate(tasks[:2]):
                    print(f"      {i+1}. {task.get('title', 'Unknown')} - {task.get('duration', 0)} min")
                    print(f"         Priority score: {task.get('priority_score', 0)}")
        else:
            print(f"   [FAIL] Failed to get available tasks: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Available tasks error: {e}")
    
    # Test 4: Get time pools
    print("\n4. Getting time pools with weather...")
    available_pool_id = None
    today = date.today()
    end_date = today + timedelta(days=7)
    
    try:
        response = requests.get(f"{BASE_URL}/time-pools", params={
            'start_date': today.isoformat(),
            'end_date': end_date.isoformat(),
            'include_weather': 'true'
        })
        
        if response.status_code == 200:
            data = response.json()
            pools = data.get('pools', [])
            
            print(f"   [OK] Found {len(pools)} time pools")
            print(f"   Total available time: {data.get('total_minutes', 0)} minutes")
            print(f"   Outdoor suitable pools: {data.get('outdoor_suitable', 0)}")
            
            available_pool_id = None
            for pool in pools[:3]:
                pool_date = pool.get('pool_date', 'Unknown')
                start_time = pool.get('start_time', '').split('T')[1][:5] if 'T' in pool.get('start_time', '') else 'Unknown'
                available = pool.get('available_minutes', 0)
                
                weather_info = pool.get('weather', {})
                weather_desc = weather_info.get('weather_condition', 'Unknown') if weather_info else 'No weather'
                
                print(f"      {pool_date} {start_time} ({available}min) - {weather_desc}")
                if available >= 30 and not available_pool_id:
                    available_pool_id = pool['id']
                    
        else:
            print(f"   [FAIL] Failed to get time pools: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Time pools error: {e}")
    
    # Test 5: Task assignment suggestions
    if available_task_id:
        print(f"\n5. Getting pool suggestions for task {available_task_id[:8]}...")
        try:
            response = requests.get(f"{BASE_URL}/task-assignments/suggest-pools/{available_task_id}")
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get('pool_suggestions', [])
                
                print(f"   [OK] Found {len(suggestions)} pool suggestions")
                for suggestion in suggestions[:2]:
                    pool = suggestion['pool']
                    score = suggestion['match_score']
                    reasons = suggestion.get('reasons', [])
                    
                    pool_date = pool.get('pool_date', 'Unknown')
                    start_time = pool.get('start_time', '').split('T')[1][:5] if 'T' in pool.get('start_time', '') else 'Unknown'
                    
                    print(f"      {pool_date} {start_time} (Score: {score:.1f})")
                    print(f"         Reasons: {', '.join(reasons[:2])}")
            else:
                print(f"   [FAIL] Failed to get suggestions: {response.status_code}")
        except Exception as e:
            print(f"   [ERROR] Suggestions error: {e}")
    
    # Test 6: Create a test assignment
    if available_task_id and available_pool_id:
        print(f"\n6. Creating test assignment...")
        try:
            assignment_data = {
                'task_id': available_task_id,
                'time_pool_id': available_pool_id,
                'allocated_minutes': 30,
                'assigned_by': 'test_script',
                'notes': 'Test assignment from queue system test'
            }
            
            response = requests.post(f"{BASE_URL}/task-assignments", json=assignment_data)
            if response.status_code == 200:
                result = response.json()
                assignment = result.get('assignment', {})
                
                print(f"   [OK] Assignment created successfully")
                print(f"      Assignment ID: {assignment.get('id', 'Unknown')[:8]}")
                print(f"      Allocated: {assignment.get('allocated_minutes', 0)} minutes")
                print(f"      Status: {assignment.get('status', 'Unknown')}")
                
                # Store assignment ID for cleanup
                test_assignment_id = assignment.get('id')
                
            else:
                print(f"   [FAIL] Failed to create assignment: {response.status_code}")
                try:
                    error_msg = response.json().get('error', 'Unknown error')
                    print(f"      Error: {error_msg}")
                except:
                    pass
        except Exception as e:
            print(f"   [ERROR] Assignment creation error: {e}")
    
    # Test 7: Check updated queue statistics
    print("\n7. Checking updated queue statistics...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"   [OK] Updated Statistics:")
            print(f"      Total tasks: {stats.get('total_tasks', 0)}")
            print(f"      Available tasks: {stats.get('available_tasks', 0)}")
            print(f"      Assigned tasks: {stats.get('assigned_tasks', 0)}")
        else:
            print(f"   [FAIL] Failed to get updated statistics: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Updated statistics error: {e}")
    
    # Test 8: Auto-assign a task
    if available_task_id:
        print(f"\n8. Testing auto-assignment...")
        try:
            response = requests.post(f"{BASE_URL}/task-assignments/auto-assign/{available_task_id}")
            if response.status_code == 200:
                result = response.json()
                print(f"   [OK] Auto-assignment successful")
                print(f"      Assignments created: {result.get('assignment_count', 0)}")
                print(f"      Message: {result.get('message', '')}")
            else:
                print(f"   [FAIL] Auto-assignment failed: {response.status_code}")
        except Exception as e:
            print(f"   [ERROR] Auto-assignment error: {e}")
    
    print("\n" + "=" * 60)
    print("Task Queue System Test Complete!")

if __name__ == "__main__":
    test_task_queue_system()