#!/usr/bin/env python3
"""
Complete YOLO System Test with Database Integration and Claude API
Tests all Phase 1 services with real Claude API integration
"""

import sys
import os
import json
import logging
from datetime import datetime, date, timedelta

# Set environment variables before importing Flask app
from pathlib import Path
env_file = Path(__file__).parent / 'flask_app' / '.env'
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
# Also load from production env if Claude key missing
if not os.getenv('CLAUDE_API_KEY'):
    prod_env = Path(__file__).parent / '.env.production' 
    if prod_env.exists():
        with open(prod_env, 'r') as f:
            for line in f:
                if line.strip().startswith('CLAUDE_API_KEY='):
                    key = line.strip().split('=', 1)[1]
                    os.environ['CLAUDE_API_KEY'] = key
                    os.environ['ANTHROPIC_API_KEY'] = key
                    break

sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

from flask_app.app import app
from flask_app.models import db, Task, Event, TimePool, Project, Initiative
from flask_app.services.project_aware_priority_service import get_project_aware_priority_service
from flask_app.services.event_aware_assignment_service import get_event_aware_assignment_service
from flask_app.services.claude_task_analyzer import ClaudeTaskAnalyzer
from flask_app.services.smart_scheduling_service import SmartSchedulingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_migration():
    """Test that new YOLO columns exist in database"""
    logger.info("\n=== Testing Database Migration ===")
    
    with app.app_context():
        try:
            # Test creating a task with new fields
            test_task = Task(
                id='yolo-test-1',
                title='Test YOLO Task',
                description='Testing AI analysis fields',
                duration=60,
                cognitive_load='medium',
                energy_level='high',
                ai_analysis='{"test": "data"}',
                last_analyzed=datetime.now()
            )
            db.session.add(test_task)
            db.session.commit()
            
            # Read back and verify
            task = Task.query.get('yolo-test-1')
            assert task.cognitive_load == 'medium'
            assert task.energy_level == 'high'
            assert task.ai_analysis == '{"test": "data"}'
            assert task.last_analyzed is not None
            
            # Clean up
            db.session.delete(task)
            db.session.commit()
            
            logger.info("PASS: Database migration successful - all YOLO columns working")
            return True
            
        except Exception as e:
            logger.error(f"FAIL: Database migration test failed: {e}")
            db.session.rollback()
            return False

def test_claude_api_integration():
    """Test Claude API with real API key"""
    logger.info("\n=== Testing Claude API Integration ===")
    
    with app.app_context():
        try:
            # Initialize analyzer
            analyzer = ClaudeTaskAnalyzer()
            
            # Check API availability
            logger.info(f"Claude API available: {analyzer.is_claude_available}")
            
            if not analyzer.is_claude_available:
                logger.warning("Claude API not available - check API key configuration")
                return False
            
            # Test quick analysis
            test_task = {
                'title': 'Design and implement a machine learning model',
                'description': 'Create a neural network for image classification using TensorFlow',
                'project_id': 'test-project'
            }
            
            # Analyze with Claude
            analysis = analyzer.analyze_task_quick(test_task)
            
            logger.info(f"Analysis result:")
            logger.info(f"  Complexity: {analysis['complexity']['score']}/10 ({analysis['complexity']['level']})")
            logger.info(f"  Time estimate: {analysis['time_estimation']['estimated_duration']} minutes")
            logger.info(f"  Suggestions: {len(analysis['suggestions'])} provided")
            logger.info(f"  Dependencies detected: {len(analysis['dependencies']['detected_dependencies'])}")
            
            # Test comprehensive analysis
            comprehensive = analyzer.analyze_task_comprehensive(test_task)
            logger.info(f"Comprehensive analysis includes: {list(comprehensive.keys())}")
            
            logger.info("PASS: Claude API integration successful")
            return True
            
        except Exception as e:
            logger.error(f"FAIL: Claude API test failed: {e}")
            return False

def test_project_aware_priority_service():
    """Test priority scoring with project context"""
    logger.info("\n=== Testing Project-Aware Priority Service ===")
    
    with app.app_context():
        try:
            service = get_project_aware_priority_service()
            
            # Create test data
            project = Project.query.first()
            if not project:
                project = Project(
                    id='test-proj-1',
                    title='Test Project',
                    priority='HIGH',
                    status='ACTIVE'
                )
                db.session.add(project)
                db.session.commit()
            
            # Test task with high priority project
            task = {
                'id': 'test-task-1',
                'title': 'Critical project task',
                'due_date': (date.today() + timedelta(days=2)).isoformat(),
                'project_id': project.id,
                'urgency': 8
            }
            
            score = service.calculate_priority_score(task)
            logger.info(f"Priority score for urgent project task: {score}/1000")
            
            # Test overdue task
            overdue_task = {
                'id': 'test-task-2',
                'title': 'Overdue task',
                'due_date': (date.today() - timedelta(days=1)).isoformat(),
                'urgency': 7
            }
            
            overdue_score = service.calculate_priority_score(overdue_task)
            logger.info(f"Priority score for overdue task: {overdue_score}/1000")
            
            assert overdue_score > score, "Overdue tasks should have higher priority"
            
            logger.info("PASS: Project-aware priority service working correctly")
            return True
            
        except Exception as e:
            logger.error(f"FAIL: Priority service test failed: {e}")
            return False

def test_event_aware_assignment():
    """Test assignment service with event conflicts"""
    logger.info("\n=== Testing Event-Aware Assignment Service ===")
    
    with app.app_context():
        try:
            service = get_event_aware_assignment_service()
            
            # Check for blocking events
            today = date.today()
            next_week = today + timedelta(days=7)
            
            # Get available pools avoiding events
            pools = service.get_available_pools_with_events(today, next_week)
            logger.info(f"Found {len(pools)} conflict-free time pools")
            
            # Test meal task preparation
            meal_result = service.prepare_meal_tasks(date_range=3)
            logger.info(f"Meal task preparation: {meal_result}")
            
            # Test recurring task handling
            recurring_result = service.handle_recurring_tasks()
            logger.info(f"Recurring task handling: {recurring_result}")
            
            logger.info("PASS: Event-aware assignment service working correctly")
            return True
            
        except Exception as e:
            logger.error(f"FAIL: Assignment service test failed: {e}")
            return False

def test_smart_scheduling_integration():
    """Test the complete smart scheduling workflow"""
    logger.info("\n=== Testing Smart Scheduling Integration ===")
    
    with app.app_context():
        try:
            service = SmartSchedulingService()
            
            # Create a test task with AI analysis
            test_task = Task(
                id='smart-test-1',
                title='Implement user authentication system',
                description='Add OAuth2 authentication with Google and GitHub providers',
                duration=180,
                project_id=Project.query.first().id if Project.query.first() else None,
                urgency=7,
                priority='high',
                status='active'
            )
            db.session.add(test_task)
            db.session.commit()
            
            # Get enriched task queue with AI analysis
            enriched_tasks = service._get_enriched_task_queue()
            
            # Find our test task
            test_task_data = next((t for t in enriched_tasks if t['id'] == 'smart-test-1'), None)
            
            if test_task_data:
                logger.info(f"Task '{test_task_data['title']}':")
                logger.info(f"  Priority score: {test_task_data['priority_score']}")
                
                # Analyze with Claude if available
                if hasattr(service, 'claude_analyzer') and service.claude_analyzer.is_claude_available:
                    analysis = service.claude_analyzer.analyze_task_quick(test_task_data)
                    
                    # Save analysis to database
                    task_db = Task.query.get('smart-test-1')
                    task_db.cognitive_load = analysis['complexity']['level']
                    task_db.energy_level = analysis['context']['energy_level']
                    task_db.ai_analysis = json.dumps(analysis)
                    task_db.last_analyzed = datetime.now()
                    db.session.commit()
                    
                    logger.info(f"  AI Analysis saved to database:")
                    logger.info(f"    Cognitive load: {task_db.cognitive_load}")
                    logger.info(f"    Energy level: {task_db.energy_level}")
            
            # Test daily scheduling routine
            results = service.daily_scheduling_routine()
            
            logger.info("\nDaily Scheduling Results:")
            logger.info(f"  Recurring tasks: {results['recurring_tasks']['processed']} processed")
            logger.info(f"  Meal tasks: {results['meal_tasks']['tasks_created']} created")
            logger.info(f"  Assignments: {results['assignments'].get('assignments_made', 0)} made")
            
            # Clean up test task
            Task.query.filter_by(id='smart-test-1').delete()
            db.session.commit()
            
            logger.info("PASS: Smart scheduling integration successful")
            return True
            
        except Exception as e:
            logger.error(f"FAIL: Smart scheduling test failed: {e}")
            db.session.rollback()
            return False

def test_complete_workflow():
    """Test a complete YOLO workflow from task creation to assignment with AI"""
    logger.info("\n=== Testing Complete YOLO Workflow ===")
    
    with app.app_context():
        try:
            # 1. Create a complex task
            task = Task(
                id='workflow-test-1',
                title='Build a real-time data pipeline with Kafka and Spark',
                description='Design and implement a streaming data pipeline for processing IoT sensor data',
                project_id=Project.query.first().id if Project.query.first() else None,
                urgency=6,
                priority='medium',
                status='active'
            )
            db.session.add(task)
            db.session.commit()
            logger.info("PASS: Task created")
            
            # 2. Analyze with Claude
            analyzer = ClaudeTaskAnalyzer()
            if analyzer.is_claude_available:
                task_dict = task.to_dict()
                analysis = analyzer.analyze_task_comprehensive(task_dict)
                
                # Save analysis
                task.cognitive_load = analysis['complexity']['level']
                task.energy_level = analysis['context']['energy_level']
                task.ai_analysis = json.dumps(analysis)
                task.last_analyzed = datetime.now()
                
                # Update duration based on AI estimate
                if 'time_estimation' in analysis:
                    task.duration = analysis['time_estimation']['estimated_duration']
                
                db.session.commit()
                logger.info(f"PASS: AI Analysis complete - complexity: {task.cognitive_load}, duration: {task.duration}min")
            
            # 3. Calculate priority score
            priority_service = get_project_aware_priority_service()
            task_dict = task.to_dict()
            priority_score = priority_service.calculate_priority_score(task_dict)
            logger.info(f"PASS: Priority score calculated: {priority_score}/1000")
            
            # 4. Find suitable time pools
            assignment_service = get_event_aware_assignment_service()
            today = date.today()
            pools = assignment_service.get_available_pools_with_events(today, today + timedelta(days=3))
            logger.info(f"PASS: Found {len(pools)} available time pools")
            
            # 5. Make smart assignment
            if pools and task.duration:
                suitable_pool = None
                for pool in pools:
                    if pool.available_minutes >= task.duration:
                        suitable_pool = pool
                        break
                
                if suitable_pool:
                    success, message, assignment = assignment_service.assign_task_to_pool(
                        task_id=task.id,
                        time_pool_id=suitable_pool.id,
                        allocated_minutes=task.duration,
                        assigned_by='yolo_test',
                        notes=f"AI-powered assignment (complexity: {task.cognitive_load})"
                    )
                    
                    if success:
                        logger.info(f"PASS: Task assigned to pool on {suitable_pool.pool_date}")
                    else:
                        logger.info(f"WARNING: Assignment failed: {message}")
                else:
                    logger.info("WARNING: No suitable time pool found")
            
            # 6. Verify database persistence
            saved_task = Task.query.get('workflow-test-1')
            assert saved_task.cognitive_load is not None
            assert saved_task.ai_analysis is not None
            assert saved_task.last_analyzed is not None
            
            # Clean up
            Task.query.filter_by(id='workflow-test-1').delete()
            db.session.commit()
            
            logger.info("PASS: Complete YOLO workflow successful!")
            return True
            
        except Exception as e:
            logger.error(f"FAIL: Complete workflow test failed: {e}")
            db.session.rollback()
            return False

def main():
    """Run all YOLO system tests"""
    logger.info("=" * 60)
    logger.info("TASKMASTER YOLO COMPLETE SYSTEM TEST")
    logger.info("Testing with Database Integration and Claude API")
    logger.info("=" * 60)
    
    tests = [
        ("Database Migration", test_database_migration),
        ("Claude API Integration", test_claude_api_integration),
        ("Project-Aware Priority Service", test_project_aware_priority_service),
        ("Event-Aware Assignment Service", test_event_aware_assignment),
        ("Smart Scheduling Integration", test_smart_scheduling_integration),
        ("Complete YOLO Workflow", test_complete_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("\nSUCCESS: ALL TESTS PASSED! YOLO System is fully operational!")
    else:
        logger.info(f"\nWARNING: {total_tests - passed_tests} tests failed. Check logs for details.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)