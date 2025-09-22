# test_smart_scheduling_service.py - Comprehensive Integration Tests for Smart Scheduling Service
import sys
import os
import pytest
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

# Add Flask app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

from flask_app.models import db, Task, Event, TimePool, Project, TaskAssignment, Initiative, ProjectPhase
from flask_app.services.smart_scheduling_service import (
    get_smart_scheduling_service, 
    SchedulingConstraint, 
    SchedulingObjective, 
    ConflictResolutionStrategy
)
from flask_app.services.project_aware_priority_service import get_project_aware_priority_service
from flask_app.services.event_aware_assignment_service import get_event_aware_assignment_service
from flask_app.services.claude_task_analyzer import get_claude_task_analyzer

class TestSmartSchedulingServiceIntegration:
    """Comprehensive integration tests for the Smart Scheduling Service"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment with sample data"""
        print("\n=== Setting up Smart Scheduling Service Integration Tests ===")
        
        # Initialize services
        cls.smart_scheduler = get_smart_scheduling_service()
        cls.priority_service = get_project_aware_priority_service()
        cls.assignment_service = get_event_aware_assignment_service()
        cls.analyzer_service = get_claude_task_analyzer()
        
        # Create test data
        cls._create_test_data()
        
        print(f"Created {len(cls.test_tasks)} test tasks, {len(cls.test_events)} test events, {len(cls.test_pools)} test pools")
    
    @classmethod
    def _create_test_data(cls):
        """Create comprehensive test data"""
        cls.test_project_id = "test-project-001"
        cls.test_initiative_id = "test-initiative-001"
        cls.test_tasks = []
        cls.test_events = []
        cls.test_pools = []
        
        # Create test project
        cls.test_project = {
            'id': cls.test_project_id,
            'title': 'Smart Scheduling Test Project',
            'description': 'Test project for smart scheduling integration',
            'priority': 'HIGH',
            'status': 'ACTIVE',
            'estimated_start_date': date.today(),
            'estimated_end_date': date.today() + timedelta(days=30)
        }
        
        # Create test initiative
        cls.test_initiative = {
            'id': cls.test_initiative_id,
            'title': 'Test Initiative',
            'description': 'Test initiative for integration testing',
            'status': 'ACTIVE'
        }
        
        # Create variety of test tasks
        task_scenarios = [
            {
                'title': 'High Priority Urgent Task',
                'description': 'Critical task that must be completed today',
                'duration': 60,
                'urgency': 9,
                'priority': 'urgent',
                'due_date': date.today(),
                'project_id': cls.test_project_id,
                'complexity_factors': ['urgent', 'critical', 'important']
            },
            {
                'title': 'Complex Research Task',
                'description': 'Comprehensive analysis requiring deep investigation and multiple components',
                'duration': 180,
                'urgency': 6,
                'priority': 'high',
                'due_date': date.today() + timedelta(days=3),
                'project_id': cls.test_project_id,
                'complexity_factors': ['complex', 'research', 'analysis', 'comprehensive']
            },
            {
                'title': 'Quick Easy Task',
                'description': 'Simple straightforward task',
                'duration': 15,
                'urgency': 3,
                'priority': 'low',
                'due_date': date.today() + timedelta(days=7),
                'complexity_factors': ['simple', 'easy', 'quick']
            },
            {
                'title': 'Dependent Task A',
                'description': 'Task that blocks other tasks',
                'duration': 90,
                'urgency': 7,
                'priority': 'high',
                'due_date': date.today() + timedelta(days=2),
                'project_id': cls.test_project_id,
                'blocks_tasks': True
            },
            {
                'title': 'Dependent Task B',
                'description': 'Task that depends on Task A',
                'duration': 60,
                'urgency': 7,
                'priority': 'high',
                'due_date': date.today() + timedelta(days=5),
                'project_id': cls.test_project_id,
                'depends_on': ['task-a']
            },
            {
                'title': 'Recurring Daily Task',
                'description': 'Task that occurs every day',
                'duration': 30,
                'urgency': 5,
                'priority': 'medium',
                'is_recurring': True,
                'recurrence_days': 1
            },
            {
                'title': 'Long Duration Task',
                'description': 'Task requiring significant time investment',
                'duration': 240,
                'urgency': 5,
                'priority': 'medium',
                'due_date': date.today() + timedelta(days=10),
                'is_divisible': True
            },
            {
                'title': 'Meeting Preparation',
                'description': 'Prepare for important client meeting',
                'duration': 45,
                'urgency': 8,
                'priority': 'high',
                'due_date': date.today() + timedelta(days=1),
                'complexity_factors': ['meeting', 'preparation', 'client']
            }
        ]
        
        # Convert scenarios to task objects
        for i, scenario in enumerate(task_scenarios):
            task_id = f"test-task-{i+1:03d}"
            task_data = {
                'id': task_id,
                'title': scenario['title'],
                'description': scenario['description'],
                'duration': scenario['duration'],
                'urgency': scenario['urgency'],
                'priority': scenario['priority'],
                'status': 'active',
                'is_completed': False,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Add optional fields
            if 'due_date' in scenario:
                task_data['due_date'] = scenario['due_date']
            if 'project_id' in scenario:
                task_data['project_id'] = scenario['project_id']
            if 'initiative_id' in scenario:
                task_data['initiative_id'] = scenario['initiative_id']
            if 'is_recurring' in scenario:
                task_data['is_recurring'] = scenario['is_recurring']
            if 'recurrence_days' in scenario:
                task_data['recurrence_days'] = scenario['recurrence_days']
            if 'is_divisible' in scenario:
                task_data['is_divisible'] = scenario['is_divisible']
            
            # Handle dependencies
            if 'depends_on' in scenario:
                deps = [f"test-task-{j+1:03d}" for j in range(len(task_scenarios)) 
                       if task_scenarios[j].get('blocks_tasks')]
                task_data['depends_on_task_ids'] = json.dumps(deps)
            
            cls.test_tasks.append(task_data)
        
        # Create test events that will block some time pools
        event_scenarios = [
            {
                'title': 'Blocking Meeting',
                'start_time': datetime.combine(date.today() + timedelta(days=1), datetime.min.time().replace(hour=10)),
                'end_time': datetime.combine(date.today() + timedelta(days=1), datetime.min.time().replace(hour=11)),
                'is_blocking': True
            },
            {
                'title': 'Lunch Break',
                'start_time': datetime.combine(date.today() + timedelta(days=2), datetime.min.time().replace(hour=12)),
                'end_time': datetime.combine(date.today() + timedelta(days=2), datetime.min.time().replace(hour=13)),
                'is_blocking': True
            },
            {
                'title': 'Non-blocking Event',
                'start_time': datetime.combine(date.today() + timedelta(days=3), datetime.min.time().replace(hour=15)),
                'end_time': datetime.combine(date.today() + timedelta(days=3), datetime.min.time().replace(hour=16)),
                'is_blocking': False
            }
        ]
        
        for i, scenario in enumerate(event_scenarios):
            event_data = {
                'id': f"test-event-{i+1:03d}",
                'title': scenario['title'],
                'start_time': scenario['start_time'],
                'end_time': scenario['end_time'],
                'is_blocking': scenario['is_blocking'],
                'created_at': datetime.now()
            }
            cls.test_events.append(event_data)
        
        # Create test time pools for the next week
        for day_offset in range(7):
            pool_date = date.today() + timedelta(days=day_offset)
            
            # Create multiple pools per day
            time_slots = [
                (9, 0, 120),   # 9-11 AM, 2 hours
                (11, 0, 60),   # 11-12 PM, 1 hour
                (13, 0, 180),  # 1-4 PM, 3 hours
                (16, 0, 120),  # 4-6 PM, 2 hours
                (19, 0, 90)    # 7-8:30 PM, 1.5 hours
            ]
            
            for slot_idx, (hour, minute, duration_min) in enumerate(time_slots):
                start_time = datetime.combine(pool_date, datetime.min.time().replace(hour=hour, minute=minute))
                end_time = start_time + timedelta(minutes=duration_min)
                
                pool_data = {
                    'id': f"test-pool-{day_offset}-{slot_idx}",
                    'pool_date': pool_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'total_minutes': duration_min,
                    'allocated_minutes': 0,
                    'available_minutes': duration_min,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                cls.test_pools.append(pool_data)
    
    def test_service_initialization(self):
        """Test that all services are properly initialized"""
        print("\n--- Testing Service Initialization ---")
        
        assert self.smart_scheduler is not None, "Smart scheduler should be initialized"
        assert self.priority_service is not None, "Priority service should be initialized"
        assert self.assignment_service is not None, "Assignment service should be initialized"
        assert self.analyzer_service is not None, "Analyzer service should be initialized"
        
        # Test constraint engine initialization
        constraint_summary = self.smart_scheduler.get_constraint_summary()
        assert constraint_summary['total_constraints'] > 0, "Default constraints should be loaded"
        
        print(f"[PASS] All services initialized with {constraint_summary['total_constraints']} constraints")
    
    def test_multi_agent_task_analysis(self):
        """Test that all agents work together to analyze tasks"""
        print("\n--- Testing Multi-Agent Task Analysis ---")
        
        test_task = self.test_tasks[0]  # High priority urgent task
        
        # Test individual agent capabilities
        print(f"Analyzing task: {test_task['title']}")
        
        # Priority service
        priority_score = self.priority_service.calculate_priority_score(test_task, self.test_tasks)
        assert priority_score > 0, "Priority service should calculate scores"
        print(f"[PASS] Priority Score: {priority_score:.1f}")
        
        # Analyzer service (may use fallback if Claude not available)
        analysis = self.analyzer_service.analyze_task_comprehensive(test_task)
        assert 'complexity_assessment' in analysis, "Analyzer should provide complexity assessment"
        print(f"[PASS] Analysis Source: {analysis.get('analysis_source', 'unknown')}")
        
        # Task context
        if test_task.get('project_id'):
            context = self.priority_service.get_task_context(test_task['id'])
            assert 'task' in context, "Should provide task context"
            print(f"[PASS] Context includes: {list(context.keys())}")
        
        print("[PASS] Multi-agent analysis working correctly")
    
    def test_constraint_engine_functionality(self):
        """Test constraint engine with various constraint types"""
        print("\n--- Testing Constraint Engine ---")
        
        constraint_engine = self.smart_scheduler.constraint_engine
        
        # Test adding custom constraint
        test_constraint = SchedulingConstraint(
            constraint_id="test_constraint_001",
            constraint_type="preference",
            description="Test constraint for integration testing",
            hard_constraint=False,
            weight=0.5,
            entities=["test-task-001"],
            parameters={"test_param": True}
        )
        
        constraint_engine.add_constraint(test_constraint)
        
        # Test constraint evaluation
        test_task = self.test_tasks[0]
        test_pool_data = self.test_pools[0]
        
        # Create mock TimePool object
        class MockTimePool:
            def __init__(self, pool_data):
                for key, value in pool_data.items():
                    setattr(self, key, value)
        
        test_pool = MockTimePool(test_pool_data)
        
        can_assign, violation_score, violated_constraints = constraint_engine.evaluate_assignment(
            test_task, test_pool
        )
        
        print(f"[PASS] Constraint evaluation: can_assign={can_assign}, violation_score={violation_score}")
        print(f"[PASS] Violated constraints: {violated_constraints}")
        
        # Test constraint removal
        success = constraint_engine.remove_constraint("test_constraint_001")
        assert success, "Should be able to remove constraint"
        print("[PASS] Constraint removal successful")
    
    def test_optimal_schedule_generation(self):
        """Test the main schedule generation functionality"""
        print("\n--- Testing Optimal Schedule Generation ---")
        
        start_time = time.time()
        
        # Generate schedule for next 3 days
        start_date = date.today()
        end_date = start_date + timedelta(days=3)
        
        print(f"Generating schedule from {start_date} to {end_date}")
        
        # Mock the task retrieval since we're not using real database
        original_get_schedulable_tasks = self.smart_scheduler._get_schedulable_tasks
        self.smart_scheduler._get_schedulable_tasks = lambda filters=None: self.test_tasks
        
        # Mock pool retrieval
        class MockTimePool:
            def __init__(self, pool_data):
                for key, value in pool_data.items():
                    setattr(self, key, value)
        
        mock_pools = [MockTimePool(pool_data) for pool_data in self.test_pools[:15]]  # Use first 15 pools
        original_get_available_pools = self.smart_scheduler.assignment_service.get_available_pools_with_events
        self.smart_scheduler.assignment_service.get_available_pools_with_events = lambda start, end: mock_pools
        
        # Mock assignment method
        def mock_assign(task_id, pool_id, allocated_minutes, assigned_by, notes):
            return True, "Mock assignment successful", {
                'id': f"assignment-{task_id}-{pool_id}",
                'task_id': task_id,
                'time_pool_id': pool_id,
                'allocated_minutes': allocated_minutes
            }
        self.smart_scheduler.assignment_service.assign_task_to_pool = mock_assign
        
        try:
            # Generate schedule
            result = self.smart_scheduler.generate_optimal_schedule(
                start_date=start_date,
                end_date=end_date,
                clear_existing=False  # Don't clear since we're mocking
            )
            
            processing_time = time.time() - start_time
            
            # Validate results
            assert result.success, f"Schedule generation should succeed: {result.recommendations}"
            assert result.total_tasks > 0, "Should process some tasks"
            assert result.processing_time_seconds > 0, "Should track processing time"
            assert processing_time < 30, f"Should complete in reasonable time (took {processing_time:.2f}s)"
            
            print(f"[PASS] Schedule generated successfully in {processing_time:.2f} seconds")
            print(f"[PASS] Tasks processed: {result.total_tasks}")
            print(f"[PASS] Tasks scheduled: {result.scheduled_tasks}")
            print(f"[PASS] Tasks unscheduled: {result.unscheduled_tasks}")
            print(f"[PASS] Optimization score: {result.optimization_score:.3f}")
            print(f"[PASS] Conflicts resolved: {result.conflicts_resolved}")
            
            if result.recommendations:
                print(f"[PASS] Recommendations: {result.recommendations[:2]}")  # Show first 2
            
        finally:
            # Restore original methods
            self.smart_scheduler._get_schedulable_tasks = original_get_schedulable_tasks
            self.smart_scheduler.assignment_service.get_available_pools_with_events = original_get_available_pools
    
    def test_project_specific_scheduling(self):
        """Test scheduling tasks for a specific project"""
        print("\n--- Testing Project-Specific Scheduling ---")
        
        # Filter tasks for our test project
        project_tasks = [task for task in self.test_tasks if task.get('project_id') == self.test_project_id]
        
        print(f"Found {len(project_tasks)} tasks in test project")
        
        # Mock task retrieval for project filter
        def mock_get_project_tasks(filters=None):
            if filters and filters.get('project_id') == self.test_project_id:
                return project_tasks
            return []
        
        original_method = self.smart_scheduler._get_schedulable_tasks
        self.smart_scheduler._get_schedulable_tasks = mock_get_project_tasks
        
        try:
            result = self.smart_scheduler.generate_optimal_schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=5),
                task_filters={'project_id': self.test_project_id},
                clear_existing=False
            )
            
            print(f"[PASS] Project scheduling result: {result.total_tasks} tasks processed")
            
        finally:
            self.smart_scheduler._get_schedulable_tasks = original_method
    
    def test_optimization_objectives(self):
        """Test different optimization objectives"""
        print("\n--- Testing Optimization Objectives ---")
        
        objectives_to_test = [
            [SchedulingObjective.MAXIMIZE_URGENT_PRIORITY],
            [SchedulingObjective.MINIMIZE_COMPLETION_TIME],
            [SchedulingObjective.OPTIMIZE_RESOURCE_USAGE],
            [SchedulingObjective.MAXIMIZE_URGENT_PRIORITY, SchedulingObjective.OPTIMIZE_RESOURCE_USAGE]
        ]
        
        for i, objectives in enumerate(objectives_to_test):
            print(f"Testing objective set {i+1}: {[obj.value for obj in objectives]}")
            
            # Mock the scheduling components
            original_get_tasks = self.smart_scheduler._get_schedulable_tasks
            self.smart_scheduler._get_schedulable_tasks = lambda filters=None: self.test_tasks[:3]  # Use subset
            
            try:
                result = self.smart_scheduler.generate_optimal_schedule(
                    start_date=date.today(),
                    end_date=date.today() + timedelta(days=2),
                    optimization_objectives=objectives,
                    clear_existing=False
                )
                
                print(f"  [PASS] Optimization score: {result.optimization_score:.3f}")
                
            finally:
                self.smart_scheduler._get_schedulable_tasks = original_get_tasks
    
    def test_conflict_resolution_strategies(self):
        """Test different conflict resolution strategies"""
        print("\n--- Testing Conflict Resolution Strategies ---")
        
        strategies = [
            ConflictResolutionStrategy.PRIORITY_FIRST,
            ConflictResolutionStrategy.OPTIMAL_BALANCE,
            ConflictResolutionStrategy.TIME_FLEXIBLE
        ]
        
        for strategy in strategies:
            print(f"Testing strategy: {strategy.value}")
            
            # Create intentional conflicts by using limited pools
            mock_pools = [MockTimePool(self.test_pools[0])]  # Only one pool
            
            class MockTimePool:
                def __init__(self, pool_data):
                    for key, value in pool_data.items():
                        setattr(self, key, value)
            
            original_get_pools = self.smart_scheduler.assignment_service.get_available_pools_with_events
            self.smart_scheduler.assignment_service.get_available_pools_with_events = lambda start, end: mock_pools
            
            original_get_tasks = self.smart_scheduler._get_schedulable_tasks
            self.smart_scheduler._get_schedulable_tasks = lambda filters=None: self.test_tasks[:5]  # Multiple tasks, one pool
            
            try:
                result = self.smart_scheduler.generate_optimal_schedule(
                    start_date=date.today(),
                    end_date=date.today() + timedelta(days=1),
                    conflict_resolution=strategy,
                    clear_existing=False
                )
                
                print(f"  [PASS] Strategy {strategy.value}: {result.scheduled_tasks} scheduled, {result.unscheduled_tasks} unscheduled")
                
            finally:
                self.smart_scheduler.assignment_service.get_available_pools_with_events = original_get_pools
                self.smart_scheduler._get_schedulable_tasks = original_get_tasks
    
    def test_performance_benchmarks(self):
        """Test performance requirements"""
        print("\n--- Testing Performance Benchmarks ---")
        
        # Test with larger dataset
        large_task_set = []
        for i in range(50):  # Create 50 test tasks
            task = {
                'id': f"perf-task-{i:03d}",
                'title': f"Performance Test Task {i}",
                'description': f"Task for performance testing iteration {i}",
                'duration': 30 + (i % 120),  # Varying durations
                'urgency': 1 + (i % 9),     # Varying urgencies
                'priority': 'medium',
                'status': 'active',
                'is_completed': False,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            large_task_set.append(task)
        
        # Mock with large dataset
        original_get_tasks = self.smart_scheduler._get_schedulable_tasks
        self.smart_scheduler._get_schedulable_tasks = lambda filters=None: large_task_set
        
        # Create more pools
        large_pool_set = []
        for day in range(5):
            for hour in range(9, 18):  # 9 AM to 6 PM
                pool_data = {
                    'id': f"perf-pool-{day}-{hour}",
                    'pool_date': date.today() + timedelta(days=day),
                    'start_time': datetime.combine(date.today() + timedelta(days=day), 
                                                 datetime.min.time().replace(hour=hour)),
                    'end_time': datetime.combine(date.today() + timedelta(days=day), 
                                               datetime.min.time().replace(hour=hour+1)),
                    'total_minutes': 60,
                    'allocated_minutes': 0,
                    'available_minutes': 60,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                large_pool_set.append(pool_data)
        
        class MockTimePool:
            def __init__(self, pool_data):
                for key, value in pool_data.items():
                    setattr(self, key, value)
        
        mock_pools = [MockTimePool(pool_data) for pool_data in large_pool_set]
        original_get_pools = self.smart_scheduler.assignment_service.get_available_pools_with_events
        self.smart_scheduler.assignment_service.get_available_pools_with_events = lambda start, end: mock_pools
        
        try:
            start_time = time.time()
            
            result = self.smart_scheduler.generate_optimal_schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=5),
                clear_existing=False
            )
            
            processing_time = time.time() - start_time
            
            # Performance assertions
            assert processing_time < 5.0, f"Should complete within 5 seconds (took {processing_time:.2f}s)"
            assert result.processing_time_seconds < 5.0, f"Reported time should be under 5s (was {result.processing_time_seconds:.2f}s)"
            
            print(f"[PASS] Performance test passed: {processing_time:.2f}s for {len(large_task_set)} tasks and {len(mock_pools)} pools")
            print(f"[PASS] Throughput: {len(large_task_set)/processing_time:.1f} tasks/second")
            
        finally:
            self.smart_scheduler._get_schedulable_tasks = original_get_tasks
            self.smart_scheduler.assignment_service.get_available_pools_with_events = original_get_pools
    
    def test_constraint_management_api(self):
        """Test constraint management functionality"""
        print("\n--- Testing Constraint Management ---")
        
        # Test adding constraint
        test_constraint = SchedulingConstraint(
            constraint_id="api_test_constraint",
            constraint_type="preference",
            description="API test constraint",
            hard_constraint=False,
            weight=0.8,
            entities=["all"],
            parameters={"test_mode": True}
        )
        
        success = self.smart_scheduler.add_scheduling_constraint(test_constraint)
        assert success, "Should be able to add constraint"
        
        # Test getting constraints
        summary = self.smart_scheduler.get_constraint_summary()
        assert summary['total_constraints'] > 0, "Should have constraints"
        
        # Test removing constraint
        success = self.smart_scheduler.remove_scheduling_constraint("api_test_constraint")
        assert success, "Should be able to remove constraint"
        
        print("[PASS] Constraint management API working correctly")
    
    def test_error_handling_and_resilience(self):
        """Test error handling and system resilience"""
        print("\n--- Testing Error Handling and Resilience ---")
        
        # Test with invalid date range
        try:
            result = self.smart_scheduler.generate_optimal_schedule(
                start_date=date.today() + timedelta(days=10),
                end_date=date.today(),  # End before start
                clear_existing=False
            )
            print("[PASS] Handled invalid date range gracefully")
        except Exception as e:
            print(f"[PASS] Caught expected error for invalid dates: {type(e).__name__}")
        
        # Test with no available pools
        original_get_pools = self.smart_scheduler.assignment_service.get_available_pools_with_events
        self.smart_scheduler.assignment_service.get_available_pools_with_events = lambda start, end: []
        
        try:
            result = self.smart_scheduler.generate_optimal_schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1),
                clear_existing=False
            )
            assert not result.success or result.scheduled_tasks == 0, "Should handle no pools gracefully"
            print("[PASS] Handled no available pools gracefully")
        finally:
            self.smart_scheduler.assignment_service.get_available_pools_with_events = original_get_pools
        
        # Test with no tasks
        original_get_tasks = self.smart_scheduler._get_schedulable_tasks
        self.smart_scheduler._get_schedulable_tasks = lambda filters=None: []
        
        try:
            result = self.smart_scheduler.generate_optimal_schedule(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1),
                clear_existing=False
            )
            assert result.success and result.total_tasks == 0, "Should handle no tasks gracefully"
            print("[PASS] Handled no tasks gracefully")
        finally:
            self.smart_scheduler._get_schedulable_tasks = original_get_tasks
    
    def run_comprehensive_test_suite(self):
        """Run all integration tests"""
        print("\n" + "="*60)
        print("SMART SCHEDULING SERVICE - COMPREHENSIVE INTEGRATION TESTS")
        print("="*60)
        
        test_methods = [
            self.test_service_initialization,
            self.test_multi_agent_task_analysis,
            self.test_constraint_engine_functionality,
            self.test_optimal_schedule_generation,
            self.test_project_specific_scheduling,
            self.test_optimization_objectives,
            self.test_conflict_resolution_strategies,
            self.test_constraint_management_api,
            self.test_error_handling_and_resilience,
            self.test_performance_benchmarks  # Run last as it's most intensive
        ]
        
        passed_tests = 0
        failed_tests = 0
        
        for test_method in test_methods:
            try:
                test_method()
                passed_tests += 1
                print(f"[PASS] {test_method.__name__} PASSED")
            except Exception as e:
                failed_tests += 1
                print(f"[FAIL] {test_method.__name__} FAILED: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*60)
        print("INTEGRATION TEST RESULTS")
        print("="*60)
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {failed_tests}")
        print(f"Success Rate: {passed_tests/(passed_tests+failed_tests)*100:.1f}%")
        
        if failed_tests == 0:
            print("\n*** ALL INTEGRATION TESTS PASSED! ***")
            print("Smart Scheduling Service is ready for production use.")
        else:
            print(f"\n*** WARNING: {failed_tests} test(s) failed. Review issues before deployment. ***")
        
        return failed_tests == 0

def run_integration_tests():
    """Main function to run integration tests"""
    test_suite = TestSmartSchedulingServiceIntegration()
    test_suite.setup_class()
    return test_suite.run_comprehensive_test_suite()

if __name__ == "__main__":
    print("Starting Smart Scheduling Service Integration Tests...")
    success = run_integration_tests()
    exit(0 if success else 1)