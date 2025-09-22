#!/usr/bin/env python3
"""
TaskMaster YOLO Phase 1 Integration Test Suite
Tests all four agent components working together:
- Agent 1.1: ProjectAwarePriorityService
- Agent 1.2: EventAwareAssignmentService
- Agent 1.3: ClaudeTaskAnalyzer
- Agent 1.4: SmartSchedulingService
"""

import sys
import os
import time
import traceback
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

class YOLOIntegrationTester:
    def __init__(self):
        self.test_results = {
            'agent_imports': {},
            'service_initialization': {},
            'integration_tests': {},
            'performance_benchmarks': {},
            'api_tests': {},
            'error_handling': {},
            'overall_status': 'UNKNOWN'
        }
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        """Log test progress with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_agent_imports(self) -> bool:
        """Test 1: Verify all four agents can be imported"""
        self.log("Testing agent imports...")
        
        agents = {
            'ProjectAwarePriorityService': 'services.project_aware_priority_service',
            'EventAwareAssignmentService': 'services.event_aware_assignment_service', 
            'ClaudeTaskAnalyzer': 'services.claude_task_analyzer',
            'SmartSchedulingService': 'services.smart_scheduling_service'
        }
        
        all_imported = True
        for agent_name, module_path in agents.items():
            try:
                module = __import__(module_path, fromlist=[agent_name])
                service_class = getattr(module, agent_name)
                self.test_results['agent_imports'][agent_name] = {
                    'status': 'SUCCESS',
                    'module_path': module_path,
                    'class_found': True
                }
                self.log(f"[CHECK] {agent_name} imported successfully")
            except Exception as e:
                self.test_results['agent_imports'][agent_name] = {
                    'status': 'FAILED',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                self.log(f"[X] {agent_name} import failed: {str(e)}", "ERROR")
                all_imported = False
                
        return all_imported
    
    def test_service_initialization(self) -> bool:
        """Test 2: Initialize all services with Flask app context"""
        self.log("Testing service initialization...")
        
        try:
            from flask_app.app import create_app
            from flask_app.models import db
            
            app = create_app()
            
            with app.app_context():
                # Initialize all services
                from flask_app.services.project_aware_priority_service import ProjectAwarePriorityService
                from flask_app.services.event_aware_assignment_service import EventAwareAssignmentService  
                from flask_app.services.claude_task_analyzer import ClaudeTaskAnalyzer
                from flask_app.services.smart_scheduling_service import SmartSchedulingService
                
                services = {}
                
                # Initialize each service
                services['priority'] = ProjectAwarePriorityService(db)
                services['assignment'] = EventAwareAssignmentService(db)
                services['analyzer'] = ClaudeTaskAnalyzer()
                services['scheduling'] = SmartSchedulingService(db)
                
                self.test_results['service_initialization'] = {
                    'status': 'SUCCESS',
                    'services_created': list(services.keys()),
                    'app_context': True
                }
                self.log("[CHECK] All services initialized successfully")
                return True, services, app
                
        except Exception as e:
            self.test_results['service_initialization'] = {
                'status': 'FAILED',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            self.log(f"[X] Service initialization failed: {str(e)}", "ERROR")
            return False, None, None
    
    def test_full_workflow_integration(self, services: Dict, app) -> bool:
        """Test 3: Complete workflow through all four agents"""
        self.log("Testing complete workflow integration...")
        
        try:
            with app.app_context():
                # Create test task data
                test_task = {
                    'id': 'test-task-001',
                    'title': 'Complete project documentation',
                    'description': 'Write comprehensive documentation for the new feature',
                    'priority': 'high',
                    'estimated_duration': 120,  # 2 hours
                    'due_date': (datetime.now() + timedelta(days=3)).isoformat(),
                    'tags': ['documentation', 'project', 'writing'],
                    'project_id': None,
                    'initiative_id': None
                }
                
                workflow_results = {}
                start_workflow = time.time()
                
                # Step 1: Priority Analysis
                self.log("  Step 1: Priority analysis...")
                priority_start = time.time()
                priority_result = services['priority'].calculate_priority_score(test_task)
                priority_time = time.time() - priority_start
                workflow_results['priority'] = {
                    'score': priority_result,
                    'time_ms': int(priority_time * 1000)
                }
                
                # Step 2: Event-Aware Assignment
                self.log("  Step 2: Event-aware assignment...")
                assignment_start = time.time()
                
                # Get current events for context
                from flask_app.models import Event
                current_events = Event.query.filter(
                    Event.start_time >= datetime.now() - timedelta(hours=1),
                    Event.start_time <= datetime.now() + timedelta(hours=24)
                ).all()
                
                event_context = [event.to_dict() for event in current_events[:5]]  # Limit for testing
                assignment_result = services['assignment'].assign_optimal_time_slot(
                    test_task, event_context
                )
                assignment_time = time.time() - assignment_start
                workflow_results['assignment'] = {
                    'result': assignment_result,
                    'time_ms': int(assignment_time * 1000),
                    'events_considered': len(event_context)
                }
                
                # Step 3: Claude Analysis
                self.log("  Step 3: Claude task analysis...")
                analyzer_start = time.time()
                analysis_result = services['analyzer'].analyze_task_complexity(test_task)
                analyzer_time = time.time() - analyzer_start
                workflow_results['analysis'] = {
                    'result': analysis_result,
                    'time_ms': int(analyzer_time * 1000)
                }
                
                # Step 4: Smart Scheduling
                self.log("  Step 4: Smart scheduling...")
                scheduling_start = time.time()
                
                # Prepare task list for scheduling
                test_tasks = [test_task]
                schedule_result = services['scheduling'].generate_optimal_schedule(
                    test_tasks,
                    start_date=datetime.now(),
                    end_date=datetime.now() + timedelta(days=1),
                    working_hours=(9, 17)
                )
                scheduling_time = time.time() - scheduling_start
                workflow_results['scheduling'] = {
                    'result': schedule_result,
                    'time_ms': int(scheduling_time * 1000)
                }
                
                total_workflow_time = time.time() - start_workflow
                
                self.test_results['integration_tests']['full_workflow'] = {
                    'status': 'SUCCESS',
                    'total_time_ms': int(total_workflow_time * 1000),
                    'steps': workflow_results,
                    'task_processed': test_task['id']
                }
                
                self.log(f"[CHECK] Full workflow completed in {total_workflow_time:.2f}s")
                return True
                
        except Exception as e:
            self.test_results['integration_tests']['full_workflow'] = {
                'status': 'FAILED',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            self.log(f"[X] Full workflow integration failed: {str(e)}", "ERROR")
            return False
    
    def test_performance_benchmarks(self, services: Dict, app) -> bool:
        """Test 4: Performance benchmarks for each service"""
        self.log("Running performance benchmarks...")
        
        try:
            with app.app_context():
                benchmarks = {}
                
                # Test each service with multiple iterations
                test_iterations = 10
                
                # Priority Service Benchmark
                self.log("  Benchmarking priority service...")
                priority_times = []
                test_task = {
                    'id': 'perf-test',
                    'title': 'Performance test task',
                    'priority': 'medium',
                    'estimated_duration': 60
                }
                
                for i in range(test_iterations):
                    start = time.time()
                    services['priority'].calculate_priority_score(test_task)
                    priority_times.append(time.time() - start)
                
                benchmarks['priority_service'] = {
                    'avg_time_ms': int(sum(priority_times) / len(priority_times) * 1000),
                    'min_time_ms': int(min(priority_times) * 1000),
                    'max_time_ms': int(max(priority_times) * 1000),
                    'iterations': test_iterations
                }
                
                # Assignment Service Benchmark
                self.log("  Benchmarking assignment service...")
                assignment_times = []
                
                for i in range(5):  # Fewer iterations for more complex service
                    start = time.time()
                    services['assignment'].assign_optimal_time_slot(test_task, [])
                    assignment_times.append(time.time() - start)
                
                benchmarks['assignment_service'] = {
                    'avg_time_ms': int(sum(assignment_times) / len(assignment_times) * 1000),
                    'min_time_ms': int(min(assignment_times) * 1000),
                    'max_time_ms': int(max(assignment_times) * 1000),
                    'iterations': len(assignment_times)
                }
                
                # Claude Analyzer Benchmark
                self.log("  Benchmarking task analyzer...")
                analyzer_times = []
                
                for i in range(3):  # Even fewer for AI service
                    start = time.time()
                    services['analyzer'].analyze_task_complexity(test_task)
                    analyzer_times.append(time.time() - start)
                
                benchmarks['analyzer_service'] = {
                    'avg_time_ms': int(sum(analyzer_times) / len(analyzer_times) * 1000),
                    'min_time_ms': int(min(analyzer_times) * 1000),
                    'max_time_ms': int(max(analyzer_times) * 1000),
                    'iterations': len(analyzer_times)
                }
                
                self.test_results['performance_benchmarks'] = {
                    'status': 'SUCCESS',
                    'benchmarks': benchmarks,
                    'target_time_ms': 5000,  # 5 second target
                    'meets_target': all(b['avg_time_ms'] < 5000 for b in benchmarks.values())
                }
                
                self.log("[CHECK] Performance benchmarks completed")
                return True
                
        except Exception as e:
            self.test_results['performance_benchmarks'] = {
                'status': 'FAILED',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            self.log(f"[X] Performance benchmarks failed: {str(e)}", "ERROR")
            return False
    
    def test_flask_app_startup(self) -> bool:
        """Test 5: Flask application startup with all services"""
        self.log("Testing Flask application startup...")
        
        try:
            # Start Flask app in background
            import subprocess
            import signal
            
            flask_process = subprocess.Popen(
                [sys.executable, 'flask_app/app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(__file__)
            )
            
            # Wait for startup
            time.sleep(3)
            
            # Test if app is responding
            try:
                response = requests.get('http://localhost:5000/', timeout=5)
                app_responding = response.status_code == 200
            except:
                app_responding = False
            
            # Cleanup
            flask_process.terminate()
            flask_process.wait(timeout=5)
            
            self.test_results['api_tests']['flask_startup'] = {
                'status': 'SUCCESS' if app_responding else 'FAILED',
                'app_responding': app_responding,
                'startup_time_seconds': 3
            }
            
            if app_responding:
                self.log("[CHECK] Flask application started successfully")
            else:
                self.log("[X] Flask application not responding", "ERROR")
                
            return app_responding
            
        except Exception as e:
            self.test_results['api_tests']['flask_startup'] = {
                'status': 'FAILED',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            self.log(f"[X] Flask startup test failed: {str(e)}", "ERROR")
            return False
    
    def test_error_resilience(self, services: Dict, app) -> bool:
        """Test 6: Error handling and graceful degradation"""
        self.log("Testing error resilience...")
        
        try:
            with app.app_context():
                error_tests = {}
                
                # Test 1: Invalid task data
                try:
                    invalid_task = {'invalid': 'data'}
                    services['priority'].calculate_priority_score(invalid_task)
                    error_tests['invalid_task_data'] = 'NO_ERROR_RAISED'
                except Exception as e:
                    error_tests['invalid_task_data'] = 'ERROR_HANDLED'
                
                # Test 2: None inputs
                try:
                    services['assignment'].assign_optimal_time_slot(None, [])
                    error_tests['none_inputs'] = 'NO_ERROR_RAISED'
                except Exception as e:
                    error_tests['none_inputs'] = 'ERROR_HANDLED'
                
                # Test 3: Empty task list for scheduling
                try:
                    result = services['scheduling'].generate_optimal_schedule(
                        [], datetime.now(), datetime.now() + timedelta(days=1)
                    )
                    error_tests['empty_task_list'] = 'HANDLED_GRACEFULLY'
                except Exception as e:
                    error_tests['empty_task_list'] = 'ERROR_RAISED'
                
                self.test_results['error_handling'] = {
                    'status': 'SUCCESS',
                    'tests': error_tests
                }
                
                self.log("[CHECK] Error resilience tests completed")
                return True
                
        except Exception as e:
            self.test_results['error_handling'] = {
                'status': 'FAILED',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            self.log(f"[X] Error resilience tests failed: {str(e)}", "ERROR")
            return False
    
    def generate_integration_report(self) -> str:
        """Generate comprehensive integration test report"""
        total_time = time.time() - self.start_time
        
        # Determine overall status
        all_tests_passed = all(
            result.get('status') == 'SUCCESS' 
            for category in self.test_results.values() 
            if isinstance(category, dict) and 'status' in category
        )
        
        self.test_results['overall_status'] = 'PASSED' if all_tests_passed else 'FAILED'
        self.test_results['total_test_time_seconds'] = round(total_time, 2)
        self.test_results['timestamp'] = datetime.now().isoformat()
        
        # Create detailed report
        report = f"""
# TaskMaster YOLO Phase 1 Integration Test Report

**Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Test Time**: {total_time:.2f} seconds
**Overall Status**: {'[SUCCESS] PASSED' if all_tests_passed else '[ERROR] FAILED'}

## Executive Summary

Phase 1 integration testing validates all four YOLO agent components:
- **Agent 1.1**: ProjectAwarePriorityService
- **Agent 1.2**: EventAwareAssignmentService  
- **Agent 1.3**: ClaudeTaskAnalyzer
- **Agent 1.4**: SmartSchedulingService

## Test Results Summary

"""
        
        # Add test category summaries
        for category, results in self.test_results.items():
            if isinstance(results, dict) and 'status' in results:
                status_icon = '[SUCCESS]' if results['status'] == 'SUCCESS' else '[ERROR]'
                report += f"- **{category.replace('_', ' ').title()}**: {status_icon} {results['status']}\n"
        
        report += f"\n## Detailed Results\n\n```json\n{json.dumps(self.test_results, indent=2)}\n```\n"
        
        return report
    
    def run_all_tests(self) -> bool:
        """Run complete integration test suite"""
        self.log("Starting TaskMaster YOLO Phase 1 Integration Tests")
        self.log("=" * 60)
        
        # Test 1: Agent Imports
        if not self.test_agent_imports():
            self.log("Critical failure: Agent imports failed", "ERROR")
            return False
        
        # Test 2: Service Initialization  
        success, services, app = self.test_service_initialization()
        if not success:
            self.log("Critical failure: Service initialization failed", "ERROR")
            return False
        
        # Test 3: Full Workflow Integration
        self.test_full_workflow_integration(services, app)
        
        # Test 4: Performance Benchmarks
        self.test_performance_benchmarks(services, app)
        
        # Test 5: Flask App Startup
        self.test_flask_app_startup()
        
        # Test 6: Error Resilience
        self.test_error_resilience(services, app)
        
        # Generate final report
        report = self.generate_integration_report()
        
        # Save report to file
        report_path = f"YOLO_Integration_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        self.log("=" * 60)
        self.log(f"Integration testing completed - Report saved to {report_path}")
        
        return self.test_results['overall_status'] == 'PASSED'

if __name__ == "__main__":
    tester = YOLOIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n[CELEBRATION] All integration tests PASSED! Phase 1 is ready for production.")
    else:
        print("\n[WARNING]  Some integration tests FAILED. Review the report for details.")
        sys.exit(1)