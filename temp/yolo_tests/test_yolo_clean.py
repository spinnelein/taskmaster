#!/usr/bin/env python3
"""
TaskMaster YOLO Phase 1 Integration Test - Clean Version
Quick validation of all four agent components
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

def test_agent_imports():
    """Test that all four agents can be imported"""
    print("Testing agent imports...")
    
    try:
        from services.project_aware_priority_service import ProjectAwarePriorityService
        print("+ ProjectAwarePriorityService imported")
    except Exception as e:
        print(f"- ProjectAwarePriorityService failed: {e}")
        return False
    
    try:
        from services.event_aware_assignment_service import EventAwareAssignmentService
        print("+ EventAwareAssignmentService imported")
    except Exception as e:
        print(f"- EventAwareAssignmentService failed: {e}")
        return False
    
    try:
        from services.claude_task_analyzer import ClaudeTaskAnalyzer
        print("+ ClaudeTaskAnalyzer imported")
    except Exception as e:
        print(f"- ClaudeTaskAnalyzer failed: {e}")
        return False
    
    try:
        from services.smart_scheduling_service import SmartSchedulingService
        print("+ SmartSchedulingService imported")
    except Exception as e:
        print(f"- SmartSchedulingService failed: {e}")
        return False
    
    return True

def test_service_initialization():
    """Test that services can be initialized"""
    print("\nTesting service initialization...")
    
    try:
        from flask_app.app import create_app
        from flask_app.models import db
        
        app = create_app()
        
        with app.app_context():
            from services.project_aware_priority_service import ProjectAwarePriorityService
            from services.event_aware_assignment_service import EventAwareAssignmentService
            from services.claude_task_analyzer import ClaudeTaskAnalyzer
            from services.smart_scheduling_service import SmartSchedulingService
            
            # Initialize services
            priority_service = ProjectAwarePriorityService()
            assignment_service = EventAwareAssignmentService()
            analyzer_service = ClaudeTaskAnalyzer()
            scheduling_service = SmartSchedulingService()
            
            print("+ All services initialized successfully")
            return True, {
                'priority': priority_service,
                'assignment': assignment_service,
                'analyzer': analyzer_service,
                'scheduling': scheduling_service
            }, app
            
    except Exception as e:
        print(f"- Service initialization failed: {e}")
        return False, None, None

def test_basic_workflow(services, app):
    """Test basic workflow through all services"""
    print("\nTesting basic workflow...")
    
    try:
        with app.app_context():
            # Create test task
            test_task = {
                'id': 'test-001',
                'title': 'Integration test task',
                'description': 'Test task for YOLO integration',
                'priority': 'high',
                'estimated_duration': 60,
                'due_date': (datetime.now() + timedelta(days=1)).isoformat(),
                'tags': ['test', 'integration']
            }
            
            # Test Priority Service
            start_time = time.time()
            priority_score = services['priority'].calculate_priority_score(test_task)
            priority_time = time.time() - start_time
            print(f"+ Priority score calculated: {priority_score} ({priority_time:.3f}s)")
            
            # Test Assignment Service - check available pools
            start_time = time.time()
            today = datetime.now().date()
            available_pools = services['assignment'].get_available_pools_with_events(
                today, today + timedelta(days=1)
            )
            assignment_time = time.time() - start_time
            print(f"+ Available pools retrieved: {len(available_pools)} pools ({assignment_time:.3f}s)")
            
            # Test Claude Analyzer (mock mode)
            start_time = time.time()
            analysis_result = services['analyzer'].analyze_task_comprehensive(test_task)
            analysis_time = time.time() - start_time
            print(f"+ Task analyzed: {analysis_result.get('complexity_score', 'N/A')} ({analysis_time:.3f}s)")
            
            # Test Smart Scheduling
            start_time = time.time()
            today = datetime.now().date()
            schedule_result = services['scheduling'].generate_optimal_schedule(
                start_date=today,
                end_date=today + timedelta(days=1)
            )
            scheduling_time = time.time() - start_time
            print(f"+ Schedule generated successfully ({scheduling_time:.3f}s)")
            
            total_time = priority_time + assignment_time + analysis_time + scheduling_time
            print(f"+ Total workflow time: {total_time:.3f}s")
            
            # Performance check
            if total_time < 5.0:
                print("+ Performance target met (< 5 seconds)")
            else:
                print(f"- Performance target missed: {total_time:.3f}s >= 5.0s")
            
            return True
            
    except Exception as e:
        print(f"- Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("TaskMaster YOLO Phase 1 Integration Test")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_agent_imports():
        print("\nCRITICAL: Agent imports failed")
        return False
    
    # Test 2: Initialization
    success, services, app = test_service_initialization()
    if not success:
        print("\nCRITICAL: Service initialization failed")
        return False
    
    # Test 3: Basic Workflow
    if not test_basic_workflow(services, app):
        print("\nWorkflow integration failed")
        return False
    
    print("\n" + "=" * 50)
    print("SUCCESS: YOLO Phase 1 Integration Tests PASSED!")
    print("\nAll four agents are working correctly:")
    print("- Agent 1.1: ProjectAwarePriorityService [OK]")
    print("- Agent 1.2: EventAwareAssignmentService [OK]")  
    print("- Agent 1.3: ClaudeTaskAnalyzer [OK]")
    print("- Agent 1.4: SmartSchedulingService [OK]")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)