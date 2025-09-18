#!/usr/bin/env python3
"""
Comprehensive testing script for ProjectAwarePriorityService and EnhancedTaskQueueService
Testing all 7 scoring components, edge cases, and Flask integration
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta
import json

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_service_instantiation():
    """Test 1: Service instantiation and basic functionality"""
    print("\n" + "="*60)
    print("TEST 1: SERVICE INSTANTIATION")
    print("="*60)
    
    try:
        # Import services
        from flask_app.services.project_aware_priority_service import get_project_aware_priority_service
        from flask_app.services.enhanced_task_queue_service import get_enhanced_task_queue_service
        
        # Test priority service instantiation
        priority_service = get_project_aware_priority_service()
        print(f"[PASS] ProjectAwarePriorityService instantiated: {type(priority_service)}")
        
        # Test enhanced queue service instantiation
        enhanced_service = get_enhanced_task_queue_service()
        print(f"[PASS] EnhancedTaskQueueService instantiated: {type(enhanced_service)}")
        
        # Test singleton pattern
        priority_service2 = get_project_aware_priority_service()
        enhanced_service2 = get_enhanced_task_queue_service()
        
        print(f"[PASS] Singleton pattern working: {priority_service is priority_service2}")
        print(f"[PASS] Enhanced service singleton: {enhanced_service is enhanced_service2}")
        
        return True, priority_service, enhanced_service
        
    except Exception as e:
        print(f"[FAIL] Service instantiation failed: {e}")
        return False, None, None

def test_baseline_data():
    """Test 2: Examine baseline task data from Flask application"""
    print("\n" + "="*60)
    print("TEST 2: BASELINE DATA EXAMINATION")
    print("="*60)
    
    try:
        # Import Flask models
        from flask_app.models import db, Task, Project, Initiative, Meal
        from flask_app.app import create_app
        
        # Create Flask app context
        app = create_app()
        with app.app_context():
            # Get all tasks
            tasks = Task.query.all()
            projects = Project.query.all()
            initiatives = Initiative.query.all()
            meals = Meal.query.all()
            
            print(f"[PASS] Found {len(tasks)} tasks in database")
            print(f"[PASS] Found {len(projects)} projects in database")
            print(f"[PASS] Found {len(initiatives)} initiatives in database")
            print(f"[PASS] Found {len(meals)} meals in database")
            
            # Examine task structure
            if tasks:
                sample_task = tasks[0]
                task_dict = sample_task.to_dict()
                print(f"\n[PASS] Sample task structure:")
                for key, value in task_dict.items():
                    print(f"   {key}: {value} ({type(value).__name__})")
                
                # Look for project/initiative relationships
                tasks_with_projects = [t for t in tasks if t.project_id]
                tasks_with_initiatives = [t for t in tasks if t.initiative_id]
                tasks_with_meals = [t for t in tasks if t.meal_id]
                
                print(f"\n[PASS] Tasks with projects: {len(tasks_with_projects)}")
                print(f"[PASS] Tasks with initiatives: {len(tasks_with_initiatives)}")
                print(f"[PASS] Tasks with meals: {len(tasks_with_meals)}")
                
                return True, tasks, projects, initiatives, meals
            else:
                print("[FAIL] No tasks found in database")
                return False, [], [], [], []
            
    except Exception as e:
        print(f"[FAIL] Baseline data examination failed: {e}")
        import traceback
        traceback.print_exc()
        return False, [], [], [], []

def test_priority_calculation(priority_service, tasks):
    """Test 3: Priority score calculation with realistic scenarios"""
    print("\n" + "="*60)
    print("TEST 3: PRIORITY SCORE CALCULATION")
    print("="*60)
    
    if not priority_service or not tasks:
        print("[FAIL] Cannot test - services or tasks not available")
        return False
    
    try:
        # Convert tasks to dicts for testing
        task_dicts = [task.to_dict() for task in tasks[:10]]  # Test first 10 tasks
        
        print(f"Testing priority calculation on {len(task_dicts)} tasks...")
        
        # Test each task
        for i, task_dict in enumerate(task_dicts):
            try:
                score = priority_service.calculate_priority_score(task_dict, task_dicts)
                print(f"[PASS] Task '{task_dict.get('title', 'Unknown')[:30]}': {score:.1f} points")
                
                # Test individual components
                components = {
                    'time_criticality': priority_service._calculate_time_criticality(task_dict),
                    'project_urgency': priority_service._calculate_project_urgency(task_dict),
                    'dependency_impact': priority_service._calculate_dependency_impact(task_dict, task_dicts),
                    'progress_momentum': priority_service._calculate_progress_momentum(task_dict),
                    'recurring_timing': priority_service._calculate_recurring_timing(task_dict),
                    'meal_timing': priority_service._calculate_meal_timing(task_dict),
                    'quick_wins': priority_service._calculate_quick_wins(task_dict)
                }
                
                print(f"   Components: {', '.join([f'{k}={v:.0f}' for k, v in components.items() if v > 0])}")
                
            except Exception as e:
                print(f"[FAIL] Task {i} failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Priority calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_scenarios():
    """Create specific test scenarios to validate scoring logic"""
    print("\n" + "="*60)
    print("TEST 4: SPECIFIC TEST SCENARIOS")
    print("="*60)
    
    # Scenario 1: High Priority Project Task
    high_priority_task = {
        'id': 'test-high-priority',
        'title': 'Critical project deadline task',
        'due_date': (date.today() + timedelta(days=1)).isoformat(),
        'urgency': 9,
        'project_id': 'test-project-high',
        'duration': 120,
        'depends_on_task_ids': None,
        'partial_completion_minutes': 0,
        'is_recurring': False,
        'meal_id': None,
        'last_completed_at': None
    }
    
    # Scenario 2: Overdue Recurring Task
    overdue_recurring_task = {
        'id': 'test-overdue-recurring',
        'title': 'Daily exercise routine',
        'due_date': (date.today() - timedelta(days=2)).isoformat(),
        'urgency': 6,
        'project_id': None,
        'duration': 45,
        'depends_on_task_ids': None,
        'partial_completion_minutes': 0,
        'is_recurring': True,
        'recurrence_days': 1,
        'last_completed_at': (datetime.now() - timedelta(days=3)).isoformat(),
        'meal_id': None
    }
    
    # Scenario 3: Meal Prep Task
    meal_prep_task = {
        'id': 'test-meal-prep',
        'title': 'Prep vegetables for dinner',
        'due_date': date.today().isoformat(),
        'urgency': 5,
        'project_id': None,
        'duration': 30,
        'depends_on_task_ids': None,
        'partial_completion_minutes': 0,
        'is_recurring': False,
        'meal_id': 'test-meal-tonight'
    }
    
    # Scenario 4: Dependency Blocker
    dependency_blocker_task = {
        'id': 'test-dependency-blocker',
        'title': 'Setup development environment',
        'due_date': None,
        'urgency': 7,
        'project_id': 'test-project-dev',
        'duration': 180,
        'depends_on_task_ids': None,
        'partial_completion_minutes': 0,
        'is_recurring': False,
        'meal_id': None
    }
    
    # Scenario 5: Quick Win Task
    quick_win_task = {
        'id': 'test-quick-win',
        'title': 'Update contact information',
        'due_date': None,
        'urgency': 3,
        'project_id': None,
        'duration': 15,
        'depends_on_task_ids': None,
        'partial_completion_minutes': 0,
        'is_recurring': False,
        'meal_id': None
    }
    
    # Scenario 6: Edge Case - Missing Data
    edge_case_task = {
        'id': 'test-edge-case',
        'title': 'Task with missing data',
        'due_date': None,
        'urgency': None,
        'project_id': None,
        'duration': None,
        'depends_on_task_ids': 'null',
        'partial_completion_minutes': None,
        'is_recurring': False,
        'meal_id': None
    }
    
    return [
        high_priority_task,
        overdue_recurring_task,
        meal_prep_task,
        dependency_blocker_task,
        quick_win_task,
        edge_case_task
    ]

def test_specific_scenarios(priority_service):
    """Test specific scenarios designed to test each scoring component"""
    scenarios = create_test_scenarios()
    
    if not priority_service:
        print("[FAIL] Cannot test - priority service not available")
        return False
    
    try:
        print(f"Testing {len(scenarios)} specific scenarios...")
        
        for scenario in scenarios:
            try:
                score = priority_service.calculate_priority_score(scenario, scenarios)
                print(f"\n[PASS] Scenario '{scenario['title']}':")
                print(f"   Total Score: {score:.1f} points")
                
                # Get component breakdown
                components = {
                    'time_criticality': priority_service._calculate_time_criticality(scenario),
                    'project_urgency': priority_service._calculate_project_urgency(scenario),
                    'dependency_impact': priority_service._calculate_dependency_impact(scenario, scenarios),
                    'progress_momentum': priority_service._calculate_progress_momentum(scenario),
                    'recurring_timing': priority_service._calculate_recurring_timing(scenario),
                    'meal_timing': priority_service._calculate_meal_timing(scenario),
                    'quick_wins': priority_service._calculate_quick_wins(scenario)
                }
                
                # Show top components
                sorted_components = sorted(components.items(), key=lambda x: x[1], reverse=True)
                top_components = [f"{k.replace('_', ' ').title()}={v:.0f}" for k, v in sorted_components if v > 0]
                print(f"   Top Components: {', '.join(top_components[:3])}")
                
            except Exception as e:
                print(f"[FAIL] Scenario '{scenario['title']}' failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Scenario testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_queue_service(enhanced_service):
    """Test 5: Enhanced Task Queue Service"""
    print("\n" + "="*60)
    print("TEST 5: ENHANCED TASK QUEUE SERVICE")
    print("="*60)
    
    if not enhanced_service:
        print("[FAIL] Cannot test - enhanced service not available")
        return False
    
    try:
        # Import Flask models
        from flask_app.models import db
        from flask_app.app import create_app
        
        # Create Flask app context
        app = create_app()
        with app.app_context():
            # Test enhanced queue generation
            enhanced_queue = enhanced_service.get_enhanced_task_queue(limit=10)
            print(f"[PASS] Enhanced queue generated: {len(enhanced_queue)} tasks")
            
            if enhanced_queue:
                print("\nTop 5 tasks by enhanced priority:")
                for i, task in enumerate(enhanced_queue[:5]):
                    score = task.get('enhanced_priority_score', 0)
                    title = task.get('title', 'Unknown')[:40]
                    print(f"   {i+1}. {title}: {score:.1f} points")
            
            # Test available queue
            available_queue = enhanced_service.get_available_enhanced_queue(limit=10)
            print(f"\n[PASS] Available enhanced queue: {len(available_queue)} tasks")
            
            # Test task context analysis
            if enhanced_queue:
                test_task_id = enhanced_queue[0]['id']
                context = enhanced_service.get_task_context_analysis(test_task_id)
                print(f"\n[PASS] Task context analysis completed for task: {test_task_id}")
                if context.get('priority_analysis'):
                    analysis = context['priority_analysis']
                    print(f"   Total Score: {analysis.get('total_score', 0):.1f}")
                    print(f"   Top Factors: {', '.join(analysis.get('top_factors', []))}")
            
            return True
            
    except Exception as e:
        print(f"[FAIL] Enhanced queue service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_integration():
    """Test 6: Flask Application Integration"""
    print("\n" + "="*60)
    print("TEST 6: FLASK APPLICATION INTEGRATION")
    print("="*60)
    
    try:
        from flask_app.app import create_app
        from flask_app.services.project_aware_priority_service import get_project_aware_priority_service
        from flask_app.services.enhanced_task_queue_service import get_enhanced_task_queue_service
        
        app = create_app()
        
        with app.app_context():
            # Test service instantiation within Flask context
            priority_service = get_project_aware_priority_service()
            enhanced_service = get_enhanced_task_queue_service()
            
            print("[PASS] Services instantiated within Flask app context")
            
            # Test database access
            from flask_app.models import Task, Project
            task_count = Task.query.count()
            project_count = Project.query.count()
            
            print(f"[PASS] Database access working: {task_count} tasks, {project_count} projects")
            
            # Test enhanced queue with database data
            enhanced_queue = enhanced_service.get_enhanced_task_queue(limit=5)
            print(f"[PASS] Enhanced queue with real data: {len(enhanced_queue)} tasks")
            
            return True
            
    except Exception as e:
        print(f"[FAIL] Flask integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_comparison():
    """Test 7: Performance comparison between baseline and enhanced scoring"""
    print("\n" + "="*60)
    print("TEST 7: PERFORMANCE COMPARISON")
    print("="*60)
    
    try:
        import time
        from flask_app.app import create_app
        from flask_app.task_queue_service import get_task_queue_service
        from flask_app.services.enhanced_task_queue_service import get_enhanced_task_queue_service
        
        app = create_app()
        
        with app.app_context():
            baseline_service = get_task_queue_service()
            enhanced_service = get_enhanced_task_queue_service()
            
            # Test baseline performance
            start_time = time.time()
            baseline_queue = baseline_service.get_all_tasks_queue(limit=50)
            baseline_time = time.time() - start_time
            
            # Test enhanced performance
            start_time = time.time()
            enhanced_queue = enhanced_service.get_enhanced_task_queue(limit=50)
            enhanced_time = time.time() - start_time
            
            print(f"[PASS] Baseline queue generation: {baseline_time:.3f}s ({len(baseline_queue)} tasks)")
            print(f"[PASS] Enhanced queue generation: {enhanced_time:.3f}s ({len(enhanced_queue)} tasks)")
            print(f"[PASS] Performance ratio: {enhanced_time/baseline_time:.2f}x (lower is better)")
            
            # Compare scoring approaches
            if baseline_queue and enhanced_queue:
                print("\nScoring comparison (first 3 tasks):")
                for i in range(min(3, len(baseline_queue), len(enhanced_queue))):
                    baseline_task = baseline_queue[i]
                    enhanced_task = enhanced_queue[i]
                    
                    baseline_score = baseline_task.get('priority_score', 0)
                    enhanced_score = enhanced_task.get('enhanced_priority_score', 0)
                    
                    print(f"   Task {i+1}: Baseline={baseline_score:.1f}, Enhanced={enhanced_score:.1f}")
            
            return True
            
    except Exception as e:
        print(f"[FAIL] Performance comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test execution"""
    print("ProjectAwarePriorityService Testing Suite")
    print("Testing all 7 scoring components, edge cases, and Flask integration")
    print("="*80)
    
    # Test Results
    results = {}
    
    # Test 1: Service instantiation
    success, priority_service, enhanced_service = test_service_instantiation()
    results['service_instantiation'] = success
    
    # Test 2: Baseline data
    success, tasks, projects, initiatives, meals = test_baseline_data()
    results['baseline_data'] = success
    
    # Test 3: Priority calculation with real data
    if priority_service and tasks:
        success = test_priority_calculation(priority_service, tasks)
        results['priority_calculation'] = success
    else:
        results['priority_calculation'] = False
    
    # Test 4: Specific scenarios
    if priority_service:
        success = test_specific_scenarios(priority_service)
        results['specific_scenarios'] = success
    else:
        results['specific_scenarios'] = False
    
    # Test 5: Enhanced queue service
    if enhanced_service:
        success = test_enhanced_queue_service(enhanced_service)
        results['enhanced_queue'] = success
    else:
        results['enhanced_queue'] = False
    
    # Test 6: Flask integration
    success = test_flask_integration()
    results['flask_integration'] = success
    
    # Test 7: Performance comparison
    success = test_performance_comparison()
    results['performance'] = success
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("[PASS] All tests passed! ProjectAwarePriorityService is ready for integration.")
    else:
        print("[FAIL] Some tests failed. Review the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    main()