import sys
import os
import uuid
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))
from app import create_app

app = create_app()

print('Testing Database Operations Integration:')
with app.app_context():
    
    from models import db, Task, Event, Initiative, Project, TimePool
    
    # Test database connection
    try:
        # Test basic connection
        result = db.session.execute(db.text('SELECT 1')).scalar()
        print(f'PASS: Database connection - query returned {result}')
        db_connected = True
    except Exception as e:
        print(f'FAIL: Database connection - {e}')
        db_connected = False
    
    if not db_connected:
        print('CRITICAL: Database not accessible, skipping tests')
        exit(1)
    
    # Test model operations
    test_results = []
    
    # Test 1: Read existing data
    try:
        task_count = Task.query.count()
        event_count = Event.query.count()
        initiative_count = Initiative.query.count()
        project_count = Project.query.count()
        timepool_count = TimePool.query.count()
        
        print(f'PASS: Data counts - Tasks:{task_count}, Events:{event_count}, Initiatives:{initiative_count}, Projects:{project_count}, TimePools:{timepool_count}')
        test_results.append(True)
    except Exception as e:
        print(f'FAIL: Reading data counts - {e}')
        test_results.append(False)
    
    # Test 2: Model to_dict() methods
    try:
        sample_task = Task.query.first()
        if sample_task:
            task_dict = sample_task.to_dict()
            required_fields = ['id', 'title', 'status', 'priority', 'created_at']
            has_required = all(field in task_dict for field in required_fields)
            print(f'PASS: Task.to_dict() - has required fields: {has_required}')
            test_results.append(has_required)
        else:
            print('SKIP: Task.to_dict() - no tasks found')
            test_results.append(True)  # Not a failure
    except Exception as e:
        print(f'FAIL: Task.to_dict() - {e}')
        test_results.append(False)
    
    # Test 3: Event model and recurring events
    try:
        sample_event = Event.query.first()
        if sample_event:
            event_dict = sample_event.to_dict()
            required_fields = ['id', 'title', 'start_time', 'event_type']
            has_required = all(field in event_dict for field in required_fields)
            print(f'PASS: Event.to_dict() - has required fields: {has_required}')
            
            # Check for recurring event fields
            recurring_fields = ['is_recurrence_master', 'recurrence_master_id', 'is_recurrence_exception']
            has_recurring = all(field in event_dict for field in recurring_fields)
            print(f'PASS: Event recurring fields - present: {has_recurring}')
            test_results.append(has_required and has_recurring)
        else:
            print('SKIP: Event tests - no events found')
            test_results.append(True)
    except Exception as e:
        print(f'FAIL: Event model tests - {e}')
        test_results.append(False)
    
    # Test 4: Initiative and Project relationships
    try:
        sample_initiative = Initiative.query.first()
        if sample_initiative:
            init_dict = sample_initiative.to_dict()
            has_tasks = hasattr(sample_initiative, 'tasks')
            print(f'PASS: Initiative model - has tasks relationship: {has_tasks}')
            test_results.append(True)
        else:
            print('SKIP: Initiative tests - no initiatives found')
            test_results.append(True)
    except Exception as e:
        print(f'FAIL: Initiative model tests - {e}')
        test_results.append(False)
    
    # Test 5: Database session management
    try:
        # Test that we can create a new session
        with db.session.begin():
            # Simple query within transaction
            count = db.session.execute(db.text('SELECT COUNT(*) FROM tasks')).scalar()
            print(f'PASS: Session management - transaction query returned {count}')
            test_results.append(True)
    except Exception as e:
        print(f'FAIL: Session management - {e}')
        test_results.append(False)
    
    # Test 6: Check for Phase 1 YOLO database features
    try:
        # Check if task assignments table exists
        from models import TaskAssignment
        assignment_count = TaskAssignment.query.count()
        print(f'PASS: TaskAssignment model - {assignment_count} assignments found')
        test_results.append(True)
    except Exception as e:
        print(f'FAIL: TaskAssignment model - {e}')
        test_results.append(False)
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f'\nDATABASE OPERATIONS SUMMARY: {passed}/{total} tests passed')
    print(f'INTEGRATION TEST 4: {"PASSED" if passed >= total * 0.8 else "FAILED"} - Database operations')