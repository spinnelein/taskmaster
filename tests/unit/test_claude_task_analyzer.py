# test_claude_task_analyzer.py - Comprehensive integration test for ClaudeTaskAnalyzer
import os
import sys
import unittest
import json
import requests
import time
from datetime import datetime, date

# Add flask_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

class TestClaudeTaskAnalyzer(unittest.TestCase):
    """Integration tests for the ClaudeTaskAnalyzer service"""
    
    def setUp(self):
        """Set up test configuration"""
        self.base_url = "http://localhost:5000"
        self.api_base = f"{self.base_url}/api"
        
        # Test task data
        self.test_task_data = {
            "title": "Implement user authentication system",
            "description": "Create a comprehensive user authentication system with login, registration, password reset, and two-factor authentication. This requires database design, API endpoints, frontend forms, and security testing.",
            "duration": 480,  # 8 hours
            "urgency": 7,
            "priority": "high",
            "status": "active"
        }
        
        self.simple_task_data = {
            "title": "Update documentation",
            "description": "Fix typos in README file",
            "duration": 15,
            "urgency": 3,
            "priority": "low"
        }
        
        # Check if Flask app is running
        self.flask_running = self._check_flask_server()
        
    def _check_flask_server(self):
        """Check if Flask server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def _create_test_task(self, task_data):
        """Create a test task via API"""
        if not self.flask_running:
            self.skipTest("Flask server not running")
        
        try:
            response = requests.post(f"{self.api_base}/tasks", json=task_data)
            if response.status_code == 201:
                return response.json()['id']
            else:
                self.skipTest(f"Failed to create test task: {response.text}")
        except Exception as e:
            self.skipTest(f"Cannot create test task: {e}")
    
    def _cleanup_task(self, task_id):
        """Clean up test task"""
        try:
            requests.delete(f"{self.api_base}/tasks/{task_id}")
        except:
            pass
    
    def test_claude_analysis_status(self):
        """Test Claude analysis service status endpoint"""
        if not self.flask_running:
            self.skipTest("Flask server not running")
        
        response = requests.get(f"{self.api_base}/claude-analysis/status")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('claude_available', data)
        self.assertIn('supported_features', data)
        self.assertIn('analysis_modes', data)
        
        # Check expected features
        expected_features = [
            'complexity_assessment',
            'dependency_insights', 
            'context_enhancement',
            'smart_suggestions',
            'project_analysis'
        ]
        
        for feature in expected_features:
            self.assertIn(feature, data['supported_features'])
        
        print(f"Claude Analysis Status: Available={data['claude_available']}")
        print(f"Supported Features: {data['supported_features']}")
    
    def test_complexity_assessment_quick(self):
        """Test quick complexity assessment without creating a task"""
        if not self.flask_running:
            self.skipTest("Flask server not running")
        
        # Test complex task
        response = requests.post(
            f"{self.api_base}/claude-analysis/complexity-assessment",
            json=self.test_task_data
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('complexity_assessment', data)
        
        complexity = data['complexity_assessment']
        self.assertIn('complexity_score', complexity)
        self.assertIn('complexity_level', complexity)
        self.assertIn('estimated_duration_minutes', complexity)
        
        # Complex task should have higher complexity score
        complex_score = complexity['complexity_score']
        self.assertGreaterEqual(complex_score, 5)
        
        print(f"Complex Task Analysis:")
        print(f"  Complexity Score: {complex_score}/10")
        print(f"  Complexity Level: {complexity['complexity_level']}")
        print(f"  Estimated Duration: {complexity['estimated_duration_minutes']} minutes")
        
        # Test simple task
        response = requests.post(
            f"{self.api_base}/claude-analysis/complexity-assessment",
            json=self.simple_task_data
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        simple_complexity = data['complexity_assessment']
        simple_score = simple_complexity['complexity_score']
        
        print(f"Simple Task Analysis:")
        print(f"  Complexity Score: {simple_score}/10")
        print(f"  Complexity Level: {simple_complexity['complexity_level']}")
        
        # Simple task should have lower complexity score
        self.assertLess(simple_score, complex_score)
    
    def test_full_task_analysis(self):
        """Test comprehensive task analysis"""
        if not self.flask_running:
            self.skipTest("Flask server not running")
        
        # Create test task
        task_id = self._create_test_task(self.test_task_data)
        
        try:
            # Get comprehensive analysis
            response = requests.get(f"{self.api_base}/tasks/{task_id}/claude-analysis")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertTrue(data['success'])
            self.assertIn('analysis', data)
            
            analysis = data['analysis']
            
            # Check all analysis components
            self.assertIn('complexity_assessment', analysis)
            self.assertIn('dependency_insights', analysis)
            self.assertIn('context_enhancement', analysis)
            self.assertIn('smart_suggestions', analysis)
            self.assertIn('analysis_source', analysis)
            
            print(f"Full Task Analysis for: {data['task_title']}")
            print(f"Analysis Source: {analysis['analysis_source']}")
            
            # Test complexity assessment
            complexity = analysis['complexity_assessment']
            print(f"Complexity Score: {complexity.get('complexity_score', 'N/A')}")
            print(f"Time Confidence: {complexity.get('time_confidence', 'N/A')}")
            
            # Test dependency insights
            dependencies = analysis['dependency_insights']
            print(f"Has Dependencies: {dependencies.get('has_dependencies', False)}")
            print(f"Dependency Signals: {dependencies.get('dependency_signals', [])}")
            
            # Test context enhancement
            context = analysis['context_enhancement']
            print(f"Categories: {context.get('categories', [])}")
            print(f"Action Words: {context.get('action_words', [])}")
            
            # Test suggestions
            suggestions = analysis['smart_suggestions']
            print(f"Optimization Suggestions: {len(suggestions)}")
            for i, suggestion in enumerate(suggestions[:3]):  # Show first 3
                print(f"  {i+1}. {suggestion.get('suggestion', 'N/A')}")
        
        finally:
            self._cleanup_task(task_id)
    
    def test_batch_analysis(self):
        """Test batch analysis of multiple tasks"""
        if not self.flask_running:
            self.skipTest("Flask server not running")
        
        # Create multiple test tasks
        task_ids = []
        test_tasks = [self.test_task_data, self.simple_task_data]
        
        try:
            for task_data in test_tasks:
                task_id = self._create_test_task(task_data)
                task_ids.append(task_id)
            
            # Perform batch analysis
            response = requests.post(
                f"{self.api_base}/tasks/claude-analysis/batch",
                json={'task_ids': task_ids}
            )
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['batch_size'], len(task_ids))
            self.assertGreater(data['successful_analyses'], 0)
            
            print(f"Batch Analysis Results:")
            print(f"  Batch Size: {data['batch_size']}")
            print(f"  Successful: {data['successful_analyses']}")
            
            # Check individual results
            for result in data['results']:
                if result['success']:
                    analysis = result['analysis']
                    complexity_score = analysis['complexity_assessment'].get('complexity_score', 'N/A')
                    print(f"  Task: {result['task_title']} - Complexity: {complexity_score}")
        
        finally:
            for task_id in task_ids:
                self._cleanup_task(task_id)
    
    def test_task_suggestions(self):
        """Test task optimization suggestions endpoint"""
        if not self.flask_running:
            self.skipTest("Flask server not running")
        
        # Create test task
        task_id = self._create_test_task(self.test_task_data)
        
        try:
            response = requests.get(f"{self.api_base}/tasks/{task_id}/suggestions")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertTrue(data['success'])
            self.assertIn('suggestions', data)
            
            suggestions = data['suggestions']
            print(f"Optimization Suggestions for: {data['task_title']}")
            print(f"Total Suggestions: {len(suggestions)}")
            
            for suggestion in suggestions:
                print(f"  Type: {suggestion.get('type', 'unknown')}")
                print(f"  Priority: {suggestion.get('priority', 'unknown')}")
                print(f"  Suggestion: {suggestion.get('suggestion', 'N/A')}")
                print(f"  Reasoning: {suggestion.get('reasoning', 'N/A')}")
                print()
        
        finally:
            self._cleanup_task(task_id)
    
    def test_caching_functionality(self):
        """Test that analysis results are cached properly"""
        if not self.flask_running:
            self.skipTest("Flask server not running")
        
        task_id = self._create_test_task(self.test_task_data)
        
        try:
            # First analysis (should cache result)
            start_time = time.time()
            response1 = requests.get(f"{self.api_base}/tasks/{task_id}/claude-analysis")
            first_duration = time.time() - start_time
            
            self.assertEqual(response1.status_code, 200)
            data1 = response1.json()
            
            # Second analysis (should use cache)
            start_time = time.time()
            response2 = requests.get(f"{self.api_base}/tasks/{task_id}/claude-analysis")
            second_duration = time.time() - start_time
            
            self.assertEqual(response2.status_code, 200)
            data2 = response2.json()
            
            # Results should be the same
            self.assertEqual(data1['analysis']['task_id'], data2['analysis']['task_id'])
            
            print(f"Caching Test:")
            print(f"  First analysis: {first_duration:.3f}s")
            print(f"  Second analysis: {second_duration:.3f}s")
            print(f"  Cache working: {second_duration < first_duration}")
        
        finally:
            self._cleanup_task(task_id)
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        if not self.flask_running:
            self.skipTest("Flask server not running")
        
        # Test invalid task ID
        response = requests.get(f"{self.api_base}/tasks/invalid-id/claude-analysis")
        self.assertEqual(response.status_code, 404)
        
        # Test batch with too many tasks
        large_batch = {'task_ids': ['id' + str(i) for i in range(15)]}
        response = requests.post(
            f"{self.api_base}/tasks/claude-analysis/batch",
            json=large_batch
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Maximum 10 tasks', data['error'])
        
        # Test empty batch
        response = requests.post(
            f"{self.api_base}/tasks/claude-analysis/batch",
            json={}
        )
        self.assertEqual(response.status_code, 400)
        
        print("Error handling tests passed")
    
    def test_performance_benchmark(self):
        """Benchmark analysis performance"""
        if not self.flask_running:
            self.skipTest("Flask server not running")
        
        print("Performance Benchmark:")
        
        # Test quick complexity assessment
        start_time = time.time()
        response = requests.post(
            f"{self.api_base}/claude-analysis/complexity-assessment",
            json=self.test_task_data
        )
        quick_duration = time.time() - start_time
        
        print(f"  Quick Complexity Assessment: {quick_duration:.3f}s")
        
        # Test full analysis
        task_id = self._create_test_task(self.test_task_data)
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_base}/tasks/{task_id}/claude-analysis")
            full_duration = time.time() - start_time
            
            print(f"  Full Task Analysis: {full_duration:.3f}s")
            
            # Performance assertions
            self.assertLess(quick_duration, 2.0, "Quick assessment should be under 2 seconds")
            self.assertLess(full_duration, 10.0, "Full analysis should be under 10 seconds")
        
        finally:
            self._cleanup_task(task_id)

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("=" * 60)
    print("CLAUDE TASK ANALYZER - COMPREHENSIVE INTEGRATION TEST")
    print("=" * 60)
    
    # Check if we can import the service directly
    try:
        from services.claude_task_analyzer import get_claude_task_analyzer
        analyzer = get_claude_task_analyzer()
        print(f"[CHECK] ClaudeTaskAnalyzer service loaded successfully")
        print(f"[CHECK] Claude API available: {analyzer.is_claude_available}")
        print(f"[CHECK] Cache directory: {analyzer.cache.cache_dir}")
    except Exception as e:
        print(f"[X] Failed to load ClaudeTaskAnalyzer service: {e}")
        return
    
    print("\nRunning API integration tests...")
    print("-" * 40)
    
    # Run the unittest suite
    unittest.main(argv=[''], exit=False, verbosity=2)

if __name__ == '__main__':
    run_comprehensive_test()