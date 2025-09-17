#!/usr/bin/env python3
"""
Check time pool state for Vacuum Room scheduling test
Focus on September 19-21, 2025 to verify snoozed_until constraints
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

from app import create_app
from models import db, Event, TimePool, Task, TaskAssignment
from background_service import background_service
from assignment_service import get_assignment_service
from datetime import date, datetime, timedelta

def check_vacuum_room_status():
    """Check current status of Vacuum Room task"""
    app = create_app()
    
    with app.app_context():
        print("=== Vacuum Room Task Analysis ===\n")
        
        # Find the snoozed Vacuum Room task (not completed)
        vacuum_task = Task.query.filter(
            Task.title == 'Vacuum Room',
            Task.is_completed == False
        ).first()
        
        if not vacuum_task:
            # Fallback: Find any vacuum room task
            vacuum_task = Task.query.filter(Task.title.ilike('%vacuum%room%')).first()
        if not vacuum_task:
            print("[ERROR] Vacuum Room task not found!")
            return None
            
        print(f"[OK] Found Vacuum Room task:")
        print(f"   ID: {vacuum_task.id}")
        print(f"   Title: {vacuum_task.title}")
        print(f"   Status: {vacuum_task.status}")
        print(f"   Is Snoozed: {vacuum_task.is_snoozed}")
        print(f"   Snoozed Until: {vacuum_task.snoozed_until}")
        print(f"   Duration: {vacuum_task.duration} minutes")
        print(f"   Is Completed: {vacuum_task.is_completed}")
        
        return vacuum_task

def check_time_pools_for_dates():
    """Check time pools for September 19-21, 2025"""
    app = create_app()
    
    with app.app_context():
        background_service.init_app(app)
        
        print("\n=== Time Pool Analysis (Sept 19-21, 2025) ===\n")
        
        dates_to_check = [
            date(2025, 9, 19),  # Before snooze end (should NOT have Vacuum Room)
            date(2025, 9, 20),  # Snooze end date (should have Vacuum Room after assignment)
            date(2025, 9, 21),  # After snooze end (should be available)
        ]
        
        for target_date in dates_to_check:
            print(f"[DATE] {target_date.strftime('%A, %B %d, %Y')}:")
            
            # Get time pools for this date
            pools = TimePool.query.filter(TimePool.pool_date == target_date).order_by(TimePool.start_time).all()
            
            if not pools:
                print("   [NONE] No time pools found")
                continue
                
            print(f"   [POOLS] Found {len(pools)} time pools:")
            total_available = 0
            
            for i, pool in enumerate(pools, 1):
                start_time = pool.start_time.strftime('%H:%M') if pool.start_time else 'Unknown'
                end_time = pool.end_time.strftime('%H:%M') if pool.end_time else 'Unknown'
                work_type = "Work" if pool.is_work_time else "Personal"
                
                print(f"      {i}. {start_time}-{end_time} ({pool.total_minutes}min total, {pool.available_minutes}min available) [{work_type}]")
                total_available += pool.available_minutes
                
                # Check for existing assignments
                assignments = TaskAssignment.query.filter_by(time_pool_id=pool.id).all()
                if assignments:
                    print(f"         [TASKS] Assignments:")
                    for assignment in assignments:
                        task = Task.query.get(assignment.task_id)
                        task_title = task.title if task else f"Task {assignment.task_id}"
                        print(f"            - {task_title} ({assignment.allocated_minutes}min, {assignment.status})")
            
            print(f"   [TOTAL] Total available time: {total_available} minutes\n")

def check_vacuum_room_assignments():
    """Check if Vacuum Room is currently assigned to any time pools"""
    app = create_app()
    
    with app.app_context():
        print("=== Current Vacuum Room Assignments ===\n")
        
        vacuum_task = Task.query.filter(
            Task.title == 'Vacuum Room',
            Task.is_completed == False
        ).first()
        if not vacuum_task:
            print("[ERROR] Vacuum Room task not found!")
            return
            
        # Check for existing assignments
        assignments = TaskAssignment.query.filter_by(task_id=vacuum_task.id).all()
        
        if not assignments:
            print("[ASSIGN] No current assignments for Vacuum Room task")
        else:
            print(f"[ASSIGN] Found {len(assignments)} assignments:")
            for assignment in assignments:
                pool = TimePool.query.get(assignment.time_pool_id)
                if pool:
                    pool_date = pool.pool_date.strftime('%B %d, %Y')
                    start_time = pool.start_time.strftime('%H:%M') if pool.start_time else 'Unknown'
                    print(f"   - {pool_date} at {start_time} - {assignment.allocated_minutes}min ({assignment.status})")
                else:
                    print(f"   - Pool {assignment.time_pool_id} - {assignment.allocated_minutes}min ({assignment.status})")

def test_assignment_service():
    """Test if assignment service would assign Vacuum Room correctly"""
    app = create_app()
    
    with app.app_context():
        print("\n=== Assignment Service Test ===\n")
        
        vacuum_task = Task.query.filter(
            Task.title == 'Vacuum Room',
            Task.is_completed == False
        ).first()
        if not vacuum_task:
            print("[ERROR] Vacuum Room task not found!")
            return
            
        assignment_service = get_assignment_service()
        
        # Test pool suggestions for Vacuum Room
        suggestions = assignment_service.suggest_pools_for_task(vacuum_task.id, limit=10)
        
        print(f"[SUGGEST] Pool suggestions for Vacuum Room task:")
        if not suggestions:
            print("   [NONE] No suitable pools found")
        else:
            print(f"   [OK] Found {len(suggestions)} suitable pools:")
            for i, suggestion in enumerate(suggestions, 1):
                pool = suggestion['pool']
                score = suggestion['match_score']
                pool_date = datetime.fromisoformat(pool['pool_date']).date()
                start_time = datetime.fromisoformat(pool['start_time']).strftime('%H:%M')
                
                print(f"      {i}. {pool_date} at {start_time} (Score: {score:.1f}, Available: {pool['available_minutes']}min)")
                
                # Show reasons
                reasons = suggestion.get('reasons', [])
                if reasons:
                    for reason in reasons[:3]:  # Show top 3 reasons
                        print(f"          - {reason}")

if __name__ == "__main__":
    print("=== TaskMaster Vacuum Room Time Pool Analysis ===\n")
    
    # Step 1: Check Vacuum Room task status
    vacuum_task = check_vacuum_room_status()
    
    # Step 2: Check time pools for target dates
    check_time_pools_for_dates()
    
    # Step 3: Check current assignments
    check_vacuum_room_assignments()
    
    # Step 4: Test assignment service
    test_assignment_service()
    
    print("\n=== Analysis Complete ===")
    print("Next step: Run bulk assignment to test the constraint system")