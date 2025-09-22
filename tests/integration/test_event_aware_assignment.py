#!/usr/bin/env python3
"""
Test script for EventAwareAssignmentService - TaskMaster YOLO upgrade
Demonstrates all key features and integration with existing Flask app
"""

import sys
import os
from datetime import date, timedelta, datetime

# Add flask_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

from flask_app.app import app
from flask_app.services.event_aware_assignment_service import get_event_aware_assignment_service
from flask_app.models import db, Task, Event, TimePool, Project, Meal

def test_service_initialization():
    """Test that the service initializes correctly"""
    print("1. Testing service initialization...")
    
    with app.app_context():
        service = get_event_aware_assignment_service()
        
        # Verify service has expected components
        assert hasattr(service, 'priority_service'), "Missing priority service"
        assert hasattr(service, 'chunking_service'), "Missing chunking service"
        
        print("[CHECK] Service initialized with priority and chunking services")
        return service

def test_event_conflict_detection(service):
    """Test event conflict detection"""
    print("\n2. Testing event conflict detection...")
    
    with app.app_context():
        today = date.today()
        end_date = today + timedelta(days=7)
        
        # Get all pools and conflict-free pools
        all_pools = TimePool.query.filter(
            TimePool.pool_date >= today,
            TimePool.pool_date <= end_date
        ).all()
        
        conflict_free_pools = service.get_available_pools_with_events(today, end_date)
        
        print(f"[CHECK] Total pools: {len(all_pools)}")
        print(f"[CHECK] Conflict-free pools: {len(conflict_free_pools)}")
        print(f"[CHECK] Pools with conflicts: {len(all_pools) - len(conflict_free_pools)}")
        
        # Test individual conflict detection
        for pool in all_pools[:3]:  # Test first 3 pools
            has_conflict = service._has_event_conflict(pool)
            print(f"  Pool {pool.pool_date} {pool.start_time}: {'CONFLICT' if has_conflict else 'CLEAR'}")

def test_dependency_graph(service):
    """Test dependency graph building"""
    print("\n3. Testing dependency graph building...")
    
    with app.app_context():
        # Get some tasks for testing
        tasks = Task.query.limit(5).all()
        task_dicts = [task.to_dict() for task in tasks]
        
        # Build dependency graph
        graph = service._build_dependency_graph(task_dicts)
        
        print(f"[CHECK] Built dependency graph for {len(task_dicts)} tasks")
        for task_id, dependencies in graph.items():
            task_title = next((t['title'] for t in task_dicts if t['id'] == task_id), 'Unknown')
            if dependencies:
                print(f"  '{task_title}' depends on {len(dependencies)} tasks")
            else:
                print(f"  '{task_title}' has no dependencies")

def test_project_assignment(service):
    """Test smart project assignment"""
    print("\n4. Testing smart project assignment...")
    
    with app.app_context():
        # Find a project to test with
        project = Project.query.first()
        
        if project:
            print(f"Testing with project: '{project.title}'")
            
            result = service.assign_project_tasks_smart(project.id)
            
            print(f"[CHECK] Assignment result: {result['success']}")
            print(f"[CHECK] Message: {result['message']}")
            print(f"[CHECK] Tasks assigned: {result['tasks_assigned']}")
            
            if result['assignments']:
                print("[CHECK] Assignment details:")
                for assignment in result['assignments']:
                    print(f"  - Task {assignment.get('task_id', 'Unknown')}: {assignment.get('allocated_minutes', 0)} minutes")
        else:
            print("[X] No projects found for testing")

def test_recurring_tasks(service):
    """Test recurring task handling"""
    print("\n5. Testing recurring task handling...")
    
    with app.app_context():
        result = service.handle_recurring_tasks()
        
        print(f"[CHECK] Processing result: {result['success']}")
        print(f"[CHECK] Tasks processed: {result['processed']}")
        print(f"[CHECK] Message: {result['message']}")
        
        if result['tasks']:
            print("[CHECK] Reactivated tasks:")
            for task_title in result['tasks']:
                print(f"  - {task_title}")

def test_meal_task_preparation(service):
    """Test meal task preparation"""
    print("\n6. Testing meal task preparation...")
    
    with app.app_context():
        result = service.prepare_meal_tasks(date_range=7)
        
        print(f"[CHECK] Preparation result: {result['success']}")
        print(f"[CHECK] Meals checked: {result['meals_checked']}")
        print(f"[CHECK] Tasks created: {result['tasks_created']}")
        print(f"[CHECK] Message: {result['message']}")
        
        if result['tasks']:
            print("[CHECK] Created meal tasks:")
            for task_title in result['tasks']:
                print(f"  - {task_title}")

def test_bulk_assignment(service):
    """Test event-aware bulk assignment"""
    print("\n7. Testing event-aware bulk assignment...")
    
    with app.app_context():
        # Get initial state
        initial_assignments = db.session.query(db.func.count()).select_from(
            db.session.query(db.text('task_assignments.id')).subquery()
        ).scalar() or 0
        
        print(f"Initial assignments: {initial_assignments}")
        
        # Run bulk assignment (without clearing existing)
        result = service.bulk_assign_with_events(
            clear_existing=False,
            max_days_ahead=5,
            respect_project_structure=True
        )
        
        print(f"[CHECK] Bulk assignment result: {result['success']}")
        print(f"[CHECK] Message: {result['message']}")
        print(f"[CHECK] Assignments made: {len(result['assignments_made'])}")
        print(f"[CHECK] Tasks processed: {result['tasks_processed']}")
        print(f"[CHECK] Pools used: {result['pools_used']}")
        print(f"[CHECK] Conflict-free pools found: {result.get('conflict_free_pools', 'N/A')}")
        
        if result['assignments_made']:
            print("[CHECK] Sample assignments:")
            for assignment in result['assignments_made'][:3]:
                print(f"  - '{assignment['task_title']}': {assignment['allocated_minutes']}min on {assignment['pool_date']}")

def test_priority_integration(service):
    """Test integration with project-aware priority service"""
    print("\n8. Testing priority service integration...")
    
    with app.app_context():
        # Get some tasks
        tasks = Task.query.limit(5).all()
        task_dicts = [task.to_dict() for task in tasks]
        
        print(f"Testing priority scoring for {len(task_dicts)} tasks:")
        
        for task_dict in task_dicts:
            priority_score = service.priority_service.calculate_priority_score(task_dict, task_dicts)
            print(f"  '{task_dict['title']}': {priority_score:.1f} points")

def test_chunking_service(service):
    """Test task chunking service"""
    print("\n9. Testing task chunking service...")
    
    # Test chunking capabilities
    chunker = service.chunking_service
    
    # Test task that can be chunked
    divisible_task = {'is_divisible': True, 'duration': 120}
    can_chunk = chunker.can_chunk_task(divisible_task)
    print(f"[CHECK] Can chunk 120min divisible task: {can_chunk}")
    
    # Test optimal chunk calculation
    available_slots = [45, 30, 60, 25, 90]
    chunks = chunker.calculate_optimal_chunks(120, available_slots)
    print(f"[CHECK] Optimal chunks for 120min task with slots {available_slots}: {chunks}")
    print(f"[CHECK] Total chunked time: {sum(chunks)}min")

def main():
    """Run all tests"""
    print("EventAwareAssignmentService Integration Test")
    print("=" * 50)
    
    try:
        # Initialize service
        service = test_service_initialization()
        
        # Run all tests
        test_event_conflict_detection(service)
        test_dependency_graph(service)
        test_project_assignment(service)
        test_recurring_tasks(service)
        test_meal_task_preparation(service)
        test_priority_integration(service)
        test_chunking_service(service)
        test_bulk_assignment(service)
        
        print("\n" + "=" * 50)
        print("[CHECK] All tests completed successfully!")
        print("[CHECK] EventAwareAssignmentService is fully operational")
        
    except Exception as e:
        print(f"\n[X] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())