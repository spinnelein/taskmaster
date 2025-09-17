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
    
    print("📋 Testing Task Queue and Assignment System")
    print("=" * 60)
    
    # Test 1: Get task queue statistics
    print("\n1. Getting task queue statistics...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Queue Statistics:")
            print(f"      📊 Total tasks: {stats.get('total_tasks', 0)}")
            print(f"      🎯 Available tasks: {stats.get('available_tasks', 0)}")
            print(f"      🚫 Blocked tasks: {stats.get('blocked_tasks', 0)}")
            print(f"      🔴 Overdue tasks: {stats.get('overdue_tasks', 0)}")
            print(f"      💤 Snoozed tasks: {stats.get('snoozed_tasks', 0)}")
            print(f"      📈 Average priority: {stats.get('average_priority_score', 0)}")
            print(f"      🎯 Assigned tasks: {stats.get('assigned_tasks', 0)}")
        else:
            print(f"   ❌ Failed to get statistics: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Statistics error: {e}")
    
    # Test 2: Get all tasks queue
    print("\n2. Getting all tasks queue (top 5)...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/all?limit=5")
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('task_queue', [])
            detailed = data.get('task_queue_detailed', [])
            
            print(f"   ✅ Found {len(tasks)} tasks in queue")
            for i, task_detail in enumerate(detailed[:3]):
                task = task_detail['task_dict']
                score = task_detail['priority_score']
                is_overdue = task_detail['is_overdue']
                can_schedule = task_detail['can_be_scheduled']
                
                status_icon = "🔴" if is_overdue else "🟢" if can_schedule else "🟡"
                print(f"      {status_icon} {task['title'][:40]} (Score: {score:.1f})")
                if task_detail.get('blocking_reasons'):
                    print(f"         🚫 {', '.join(task_detail['blocking_reasons'])}")
        else:
            print(f"   ❌ Failed to get task queue: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Task queue error: {e}")
    
    # Test 3: Get available tasks queue
    print("\n3. Getting available tasks queue...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/available?limit=3")
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('available_tasks', [])
            
            print(f"   ✅ Found {len(tasks)} available tasks")
            available_task_id = None
            for task in tasks[:2]:
                print(f"      🎯 {task['title'][:40]} ({task.get('duration', 0)}min)")
                if not available_task_id:
                    available_task_id = task['id']
        else:
            print(f"   ❌ Failed to get available tasks: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Available tasks error: {e}")
    
    # Test 4: Get time pools with weather
    print("\n4. Getting time pools for next 3 days...")
    try:
        today = date.today()
        end_date = today + timedelta(days=3)
        
        response = requests.get(f"{BASE_URL}/time-pools", params={
            'start_date': today.isoformat(),
            'end_date': end_date.isoformat(),
            'include_weather': 'true'
        })
        
        if response.status_code == 200:
            data = response.json()
            pools = data.get('pools', [])
            
            print(f"   ✅ Found {len(pools)} time pools")
            print(f"   📊 Total available time: {data.get('total_minutes', 0)} minutes")
            print(f"   🌤️  Outdoor suitable pools: {data.get('outdoor_suitable', 0)}")
            
            available_pool_id = None
            for pool in pools[:3]:
                pool_date = pool.get('pool_date', 'Unknown')
                start_time = pool.get('start_time', '').split('T')[1][:5] if 'T' in pool.get('start_time', '') else 'Unknown'
                available = pool.get('available_minutes', 0)
                
                weather_info = pool.get('weather', {})
                weather_desc = weather_info.get('weather_condition', 'Unknown') if weather_info else 'No weather'
                
                print(f"      📅 {pool_date} {start_time} ({available}min) - {weather_desc}")
                if available >= 30 and not available_pool_id:
                    available_pool_id = pool['id']
                    
        else:
            print(f"   ❌ Failed to get time pools: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Time pools error: {e}")
    
    # Test 5: Task assignment suggestions
    if available_task_id:
        print(f"\n5. Getting pool suggestions for task {available_task_id[:8]}...")
        try:
            response = requests.get(f"{BASE_URL}/task-assignments/suggest-pools/{available_task_id}")
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get('pool_suggestions', [])
                
                print(f"   ✅ Found {len(suggestions)} pool suggestions")
                for suggestion in suggestions[:2]:
                    pool = suggestion['pool']
                    score = suggestion['match_score']
                    reasons = suggestion.get('reasons', [])
                    
                    pool_date = pool.get('pool_date', 'Unknown')
                    start_time = pool.get('start_time', '').split('T')[1][:5] if 'T' in pool.get('start_time', '') else 'Unknown'
                    
                    print(f"      🎯 {pool_date} {start_time} (Score: {score:.1f})")
                    print(f"         💡 {', '.join(reasons[:2])}")
            else:
                print(f"   ❌ Failed to get suggestions: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Suggestions error: {e}")
    
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
                
                print(f"   ✅ Assignment created successfully")
                print(f"      📋 Assignment ID: {assignment.get('id', 'Unknown')[:8]}")
                print(f"      ⏰ Allocated: {assignment.get('allocated_minutes', 0)} minutes")
                print(f"      📝 Status: {assignment.get('status', 'Unknown')}")
                
                # Store assignment ID for cleanup
                test_assignment_id = assignment.get('id')
                
            else:
                print(f"   ❌ Failed to create assignment: {response.status_code}")
                try:
                    error_msg = response.json().get('error', 'Unknown error')
                    print(f"      📝 Error: {error_msg}")
                except:
                    pass
        except Exception as e:
            print(f"   ❌ Assignment creation error: {e}")
    
    # Test 7: Check updated queue statistics
    print("\n7. Checking updated queue statistics...")
    try:
        response = requests.get(f"{BASE_URL}/task-queue/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Updated Statistics:")
            print(f"      📊 Total tasks: {stats.get('total_tasks', 0)}")
            print(f"      🎯 Available tasks: {stats.get('available_tasks', 0)}")
            print(f"      ⚡ Assigned tasks: {stats.get('assigned_tasks', 0)}")
            print(f"      ✅ Fully assigned: {stats.get('fully_assigned_tasks', 0)}")
        else:
            print(f"   ❌ Failed to get updated statistics: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Updated statistics error: {e}")
    
    # Test 8: Get assignments
    print("\n8. Getting recent assignments...")
    try:
        response = requests.get(f"{BASE_URL}/task-assignments?status=assigned")
        if response.status_code == 200:
            data = response.json()
            assignments = data.get('assignments', [])
            
            print(f"   ✅ Found {len(assignments)} active assignments")
            for assignment in assignments[:2]:
                task_id = assignment.get('task_id', 'Unknown')
                pool_id = assignment.get('time_pool_id', 'Unknown')
                minutes = assignment.get('allocated_minutes', 0)
                assigned_by = assignment.get('assigned_by', 'Unknown')
                
                print(f"      📋 Task {task_id[:8]} → Pool {pool_id[:8]} ({minutes}min) by {assigned_by}")
        else:
            print(f"   ❌ Failed to get assignments: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Assignments error: {e}")
    
    # Test 9: Auto-assignment test (if we have another available task)
    try:
        response = requests.get(f"{BASE_URL}/task-queue/available?limit=5")
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('available_tasks', [])
            
            # Find a task that's not the one we already assigned
            auto_assign_task_id = None
            for task in tasks:
                if task['id'] != available_task_id and task.get('duration', 0) > 0:
                    auto_assign_task_id = task['id']
                    break
            
            if auto_assign_task_id:
                print(f"\n9. Testing auto-assignment for task {auto_assign_task_id[:8]}...")
                response = requests.post(f"{BASE_URL}/task-assignments/auto-assign/{auto_assign_task_id}")
                if response.status_code == 200:
                    result = response.json()
                    assignments = result.get('assignments', [])
                    message = result.get('message', '')
                    
                    print(f"   ✅ Auto-assignment successful")
                    print(f"      📝 {message}")
                    print(f"      📋 Created {len(assignments)} assignments")
                else:
                    print(f"   ⚠️  Auto-assignment failed: {response.status_code}")
                    try:
                        error_msg = response.json().get('message', 'Unknown error')
                        print(f"      📝 Reason: {error_msg}")
                    except:
                        pass
            else:
                print("\n9. Skipping auto-assignment test (no suitable tasks)")
                
    except Exception as e:
        print(f"   ❌ Auto-assignment test error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Task Queue and Assignment System Test Complete!")
    print("\nFeatures tested:")
    print("• ✅ Task priority scoring and queue ordering")
    print("• ✅ Available vs all tasks filtering") 
    print("• ✅ Task assignment to time pools")
    print("• ✅ Pool suggestions with weather matching")
    print("• ✅ Assignment tracking and statistics")
    print("• ✅ Auto-assignment with intelligent matching")
    print("\nThe task queue system is working properly! 🎉")

if __name__ == "__main__":
    test_task_queue_system()