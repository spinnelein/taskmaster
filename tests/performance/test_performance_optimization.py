#!/usr/bin/env python3
"""
TaskMaster Performance Optimization Test Suite

Comprehensive testing for the performance optimization implementation including:
- Cache service functionality
- Performance monitoring
- Database optimization
- Benchmarking capabilities
- Middleware integration
"""

import time
import json
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

# Test configuration
BASE_URL = 'http://localhost:5000'
TEST_TIMEOUT = 30
PERFORMANCE_THRESHOLDS = {
    'response_time_warning': 1000,  # ms
    'response_time_critical': 5000,  # ms
    'cache_hit_rate_minimum': 50,   # %
    'error_rate_maximum': 5,        # %
}

class PerformanceTestRunner:
    """Main test runner for performance optimization features."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
        # Test endpoints
        self.endpoints = {
            'health': '/health',
            'performance_health': '/api/performance/health',
            'performance_stats': '/api/performance/stats',
            'cache_stats': '/api/performance/cache',
            'monitoring': '/api/performance/monitoring',
            'database_analysis': '/api/performance/database',
            'tasks_v2': '/api/v2/tasks',
            'events_v2': '/api/v2/events',
            'schedule': '/api/schedule/queue'
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance optimization tests."""
        print("=" * 60)
        print("TaskMaster Performance Optimization Test Suite")
        print("=" * 60)
        
        overall_results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'tests': {},
            'summary': {},
            'recommendations': []
        }
        
        # Test 1: Basic connectivity and health checks
        print("\n1. Testing Basic Connectivity...")
        overall_results['tests']['connectivity'] = self.test_connectivity()
        
        # Test 2: Performance services availability
        print("\n2. Testing Performance Services...")
        overall_results['tests']['services'] = self.test_performance_services()
        
        # Test 3: Cache system functionality
        print("\n3. Testing Cache System...")
        overall_results['tests']['cache'] = self.test_cache_system()
        
        # Test 4: Performance monitoring
        print("\n4. Testing Performance Monitoring...")
        overall_results['tests']['monitoring'] = self.test_performance_monitoring()
        
        # Test 5: Database optimization
        print("\n5. Testing Database Optimization...")
        overall_results['tests']['database'] = self.test_database_optimization()
        
        # Test 6: Response optimization
        print("\n6. Testing Response Optimization...")
        overall_results['tests']['response'] = self.test_response_optimization()
        
        # Test 7: Load testing
        print("\n7. Testing Load Performance...")
        overall_results['tests']['load'] = self.test_load_performance()
        
        # Test 8: Benchmarking system
        print("\n8. Testing Benchmarking System...")
        overall_results['tests']['benchmarking'] = self.test_benchmarking_system()
        
        # Generate summary and recommendations
        overall_results['summary'] = self.generate_summary(overall_results['tests'])
        overall_results['recommendations'] = self.generate_recommendations(overall_results['tests'])
        
        self.print_final_report(overall_results)
        return overall_results
    
    def test_connectivity(self) -> Dict[str, Any]:
        """Test basic application connectivity."""
        results = {'passed': 0, 'failed': 0, 'details': []}
        
        # Test basic health endpoint
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                results['passed'] += 1
                results['details'].append("[CHECK] Basic health check passed")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Basic health check failed: HTTP {response.status_code}")
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Basic health check error: {e}")
        
        # Test performance health endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/performance/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results['passed'] += 1
                    results['details'].append("[CHECK] Performance health check passed")
                    
                    # Check service availability
                    services = data.get('data', {}).get('services', {})
                    for service, available in services.items():
                        if available:
                            results['details'].append(f"  [CHECK] {service} service available")
                        else:
                            results['details'].append(f"  ⚠ {service} service not available")
                else:
                    results['failed'] += 1
                    results['details'].append("[X] Performance health check returned error status")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Performance health check failed: HTTP {response.status_code}")
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Performance health check error: {e}")
        
        return results
    
    def test_performance_services(self) -> Dict[str, Any]:
        """Test availability and functionality of performance services."""
        results = {'passed': 0, 'failed': 0, 'details': [], 'metrics': {}}
        
        # Test performance stats endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/performance/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results['passed'] += 1
                    results['details'].append("[CHECK] Performance stats endpoint working")
                    
                    # Extract key metrics
                    stats_data = data.get('data', {})
                    results['metrics']['cache_available'] = 'cache' in stats_data
                    results['metrics']['monitoring_available'] = 'monitoring' in stats_data
                    results['metrics']['database_available'] = 'database' in stats_data
                    
                else:
                    results['failed'] += 1
                    results['details'].append("[X] Performance stats returned error")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Performance stats failed: HTTP {response.status_code}")
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Performance stats error: {e}")
        
        return results
    
    def test_cache_system(self) -> Dict[str, Any]:
        """Test cache system functionality."""
        results = {'passed': 0, 'failed': 0, 'details': [], 'metrics': {}}
        
        # Test cache stats
        try:
            response = self.session.get(f"{self.base_url}/api/performance/cache", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results['passed'] += 1
                    results['details'].append("[CHECK] Cache stats endpoint working")
                    
                    cache_data = data.get('data', {})
                    results['metrics']['redis_available'] = cache_data.get('redis_available', False)
                    results['metrics']['hit_rate'] = cache_data.get('hit_rate', 0)
                    results['metrics']['total_requests'] = cache_data.get('total_requests', 0)
                    
                    if results['metrics']['redis_available']:
                        results['details'].append("  [CHECK] Redis cache available")
                    else:
                        results['details'].append("  ⚠ Redis cache not available (using memory cache only)")
                else:
                    results['failed'] += 1
                    results['details'].append("[X] Cache stats returned error")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Cache stats failed: HTTP {response.status_code}")
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Cache stats error: {e}")
        
        # Test cache operations
        try:
            # Clear cache
            clear_response = self.session.post(
                f"{self.base_url}/api/performance/cache",
                json={'operation': 'clear'},
                timeout=10
            )
            
            if clear_response.status_code == 200:
                results['passed'] += 1
                results['details'].append("[CHECK] Cache clear operation working")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Cache clear failed: HTTP {clear_response.status_code}")
                
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Cache operations error: {e}")
        
        return results
    
    def test_performance_monitoring(self) -> Dict[str, Any]:
        """Test performance monitoring functionality."""
        results = {'passed': 0, 'failed': 0, 'details': [], 'metrics': {}}
        
        # Generate some requests to monitor
        for endpoint in ['/api/v2/tasks', '/api/v2/events', '/health']:
            try:
                self.session.get(f"{self.base_url}{endpoint}", timeout=5)
            except:
                pass
        
        # Test monitoring data
        try:
            response = self.session.get(f"{self.base_url}/api/performance/monitoring", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results['passed'] += 1
                    results['details'].append("[CHECK] Performance monitoring working")
                    
                    monitoring_data = data.get('data', {})
                    
                    # Check endpoint metrics
                    endpoints = monitoring_data.get('endpoints', {})
                    results['metrics']['monitored_endpoints'] = len(endpoints)
                    
                    if endpoints:
                        results['details'].append(f"  [CHECK] Monitoring {len(endpoints)} endpoints")
                        
                        # Check for response time data
                        for endpoint, metrics in endpoints.items():
                            avg_time = metrics.get('avg_response_time', 0)
                            if avg_time > 0:
                                results['details'].append(f"    {endpoint}: {avg_time:.2f}ms avg")
                    
                    # Check memory monitoring
                    memory = monitoring_data.get('memory', {})
                    if memory:
                        results['metrics']['memory_usage_mb'] = memory.get('rss_mb', 0)
                        results['details'].append(f"  [CHECK] Memory usage: {memory.get('rss_mb', 0):.1f}MB")
                    
                else:
                    results['failed'] += 1
                    results['details'].append("[X] Performance monitoring returned error")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Performance monitoring failed: HTTP {response.status_code}")
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Performance monitoring error: {e}")
        
        return results
    
    def test_database_optimization(self) -> Dict[str, Any]:
        """Test database optimization features."""
        results = {'passed': 0, 'failed': 0, 'details': [], 'metrics': {}}
        
        # Test database analysis
        try:
            response = self.session.get(
                f"{self.base_url}/api/performance/database?action=analyze",
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results['passed'] += 1
                    results['details'].append("[CHECK] Database schema analysis working")
                    
                    analysis_data = data.get('data', {})
                    
                    # Check analysis results
                    stats = analysis_data.get('statistics', {})
                    results['metrics']['total_tables'] = stats.get('total_tables', 0)
                    results['metrics']['total_indexes'] = stats.get('total_indexes', 0)
                    results['metrics']['missing_indexes'] = stats.get('missing_indexes', 0)
                    
                    results['details'].append(f"  [CHECK] Found {stats.get('total_tables', 0)} tables")
                    results['details'].append(f"  [CHECK] Found {stats.get('total_indexes', 0)} existing indexes")
                    
                    if stats.get('missing_indexes', 0) > 0:
                        results['details'].append(f"  ⚠ {stats.get('missing_indexes', 0)} index recommendations")
                else:
                    results['failed'] += 1
                    results['details'].append("[X] Database analysis returned error")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Database analysis failed: HTTP {response.status_code}")
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Database analysis error: {e}")
        
        # Test optimization stats
        try:
            response = self.session.get(f"{self.base_url}/api/performance/database", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results['passed'] += 1
                    results['details'].append("[CHECK] Database optimization stats working")
                    
                    stats_data = data.get('data', {})
                    results['metrics']['queries_analyzed'] = stats_data.get('queries_analyzed', 0)
                    results['metrics']['slow_queries'] = stats_data.get('slow_queries_detected', 0)
                    
                else:
                    results['failed'] += 1
                    results['details'].append("[X] Database optimization stats returned error")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Database optimization stats failed: HTTP {response.status_code}")
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Database optimization stats error: {e}")
        
        return results
    
    def test_response_optimization(self) -> Dict[str, Any]:
        """Test response optimization features like compression."""
        results = {'passed': 0, 'failed': 0, 'details': [], 'metrics': {}}
        
        # Test gzip compression
        try:
            headers = {'Accept-Encoding': 'gzip'}
            response = self.session.get(
                f"{self.base_url}/api/v2/tasks?limit=50",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results['passed'] += 1
                
                # Check if response was compressed
                if 'gzip' in response.headers.get('Content-Encoding', ''):
                    results['details'].append("[CHECK] Response compression working")
                    results['metrics']['compression_enabled'] = True
                else:
                    results['details'].append("⚠ Response not compressed (may be too small)")
                    results['metrics']['compression_enabled'] = False
                
                # Check performance headers
                if 'X-Response-Time' in response.headers:
                    response_time = response.headers['X-Response-Time']
                    results['details'].append(f"  [CHECK] Response time header: {response_time}")
                    results['metrics']['response_time_header'] = True
                
                if 'X-Cache-Hit-Rate' in response.headers:
                    hit_rate = response.headers['X-Cache-Hit-Rate']
                    results['details'].append(f"  [CHECK] Cache hit rate header: {hit_rate}")
                    results['metrics']['cache_headers'] = True
                
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Response optimization test failed: HTTP {response.status_code}")
                
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Response optimization error: {e}")
        
        return results
    
    def test_load_performance(self) -> Dict[str, Any]:
        """Test application performance under load."""
        results = {'passed': 0, 'failed': 0, 'details': [], 'metrics': {}}
        
        # Simple concurrent request test
        def make_request(endpoint):
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                return {
                    'success': response.status_code == 200,
                    'response_time': (end_time - start_time) * 1000,
                    'status_code': response.status_code
                }
            except Exception as e:
                return {
                    'success': False,
                    'response_time': 0,
                    'error': str(e)
                }
        
        # Test with 10 concurrent requests
        threads = []
        request_results = []
        
        for i in range(10):
            endpoint = ['/api/v2/tasks', '/api/v2/events', '/health'][i % 3]
            thread = threading.Thread(target=lambda: request_results.append(make_request(endpoint)))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=15)
        
        if request_results:
            successful_requests = [r for r in request_results if r.get('success')]
            response_times = [r['response_time'] for r in successful_requests]
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                success_rate = len(successful_requests) / len(request_results) * 100
                
                results['metrics']['avg_response_time'] = avg_response_time
                results['metrics']['max_response_time'] = max_response_time
                results['metrics']['success_rate'] = success_rate
                
                if success_rate >= 90:
                    results['passed'] += 1
                    results['details'].append(f"[CHECK] Load test passed: {success_rate:.1f}% success rate")
                else:
                    results['failed'] += 1
                    results['details'].append(f"[X] Load test failed: {success_rate:.1f}% success rate")
                
                results['details'].append(f"  Average response time: {avg_response_time:.2f}ms")
                results['details'].append(f"  Maximum response time: {max_response_time:.2f}ms")
                
                if avg_response_time < PERFORMANCE_THRESHOLDS['response_time_warning']:
                    results['details'].append("  [CHECK] Response times within acceptable range")
                else:
                    results['details'].append("  ⚠ Response times above warning threshold")
            else:
                results['failed'] += 1
                results['details'].append("[X] No successful responses in load test")
        else:
            results['failed'] += 1
            results['details'].append("[X] Load test failed to complete")
        
        return results
    
    def test_benchmarking_system(self) -> Dict[str, Any]:
        """Test the benchmarking system functionality."""
        results = {'passed': 0, 'failed': 0, 'details': [], 'metrics': {}}
        
        # Test benchmark execution
        try:
            benchmark_config = {
                'test_name': f'test_benchmark_{int(time.time())}',
                'test_type': 'load',
                'endpoints': ['health', 'tasks_list'],
                'config': {
                    'concurrent_users': 3,
                    'requests_per_user': 5,
                    'ramp_up_time': 2,
                    'timeout': 10
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/performance/benchmark",
                json=benchmark_config,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results['passed'] += 1
                    results['details'].append("[CHECK] Benchmarking system working")
                    
                    benchmark_data = data.get('data', {})
                    results['metrics']['total_requests'] = benchmark_data.get('total_requests', 0)
                    results['metrics']['avg_response_time'] = benchmark_data.get('avg_response_time', 0)
                    results['metrics']['requests_per_second'] = benchmark_data.get('requests_per_second', 0)
                    results['metrics']['error_rate'] = benchmark_data.get('error_rate', 0)
                    
                    results['details'].append(f"  Total requests: {benchmark_data.get('total_requests', 0)}")
                    results['details'].append(f"  Average response time: {benchmark_data.get('avg_response_time', 0):.2f}ms")
                    results['details'].append(f"  Requests per second: {benchmark_data.get('requests_per_second', 0):.2f}")
                    results['details'].append(f"  Error rate: {benchmark_data.get('error_rate', 0):.2f}%")
                    
                else:
                    results['failed'] += 1
                    results['details'].append("[X] Benchmark execution returned error")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Benchmark execution failed: HTTP {response.status_code}")
                
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Benchmarking system error: {e}")
        
        # Test benchmark history
        try:
            response = self.session.get(f"{self.base_url}/api/performance/benchmark/history", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results['passed'] += 1
                    results['details'].append("[CHECK] Benchmark history retrieval working")
                    
                    benchmarks = data.get('data', {}).get('benchmarks', [])
                    results['metrics']['benchmark_history_count'] = len(benchmarks)
                    
                else:
                    results['failed'] += 1
                    results['details'].append("[X] Benchmark history returned error")
            else:
                results['failed'] += 1
                results['details'].append(f"[X] Benchmark history failed: HTTP {response.status_code}")
                
        except Exception as e:
            results['failed'] += 1
            results['details'].append(f"[X] Benchmark history error: {e}")
        
        return results
    
    def generate_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall test summary."""
        total_passed = sum(test.get('passed', 0) for test in test_results.values())
        total_failed = sum(test.get('failed', 0) for test in test_results.values())
        total_tests = total_passed + total_failed
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Performance metrics aggregation
        avg_response_times = []
        cache_hit_rates = []
        memory_usage = []
        
        for test_result in test_results.values():
            metrics = test_result.get('metrics', {})
            
            if 'avg_response_time' in metrics:
                avg_response_times.append(metrics['avg_response_time'])
            
            if 'hit_rate' in metrics:
                cache_hit_rates.append(metrics['hit_rate'])
            
            if 'memory_usage_mb' in metrics:
                memory_usage.append(metrics['memory_usage_mb'])
        
        summary = {
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'success_rate': round(success_rate, 1),
            'overall_status': 'PASS' if success_rate >= 80 else 'FAIL',
            'performance_metrics': {
                'avg_response_time': round(sum(avg_response_times) / len(avg_response_times), 2) if avg_response_times else 0,
                'cache_hit_rate': round(sum(cache_hit_rates) / len(cache_hit_rates), 2) if cache_hit_rates else 0,
                'memory_usage_mb': round(sum(memory_usage) / len(memory_usage), 2) if memory_usage else 0
            }
        }
        
        return summary
    
    def generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Cache recommendations
        cache_test = test_results.get('cache', {})
        if cache_test.get('metrics', {}).get('redis_available') is False:
            recommendations.append("Install and configure Redis for better caching performance")
        
        # Performance recommendations
        monitoring_test = test_results.get('monitoring', {})
        memory_usage = monitoring_test.get('metrics', {}).get('memory_usage_mb', 0)
        if memory_usage > 200:
            recommendations.append(f"Memory usage is high ({memory_usage:.1f}MB) - consider optimization")
        
        # Response time recommendations
        load_test = test_results.get('load', {})
        avg_response_time = load_test.get('metrics', {}).get('avg_response_time', 0)
        if avg_response_time > PERFORMANCE_THRESHOLDS['response_time_warning']:
            recommendations.append(f"Average response time ({avg_response_time:.2f}ms) exceeds warning threshold")
        
        # Database recommendations
        db_test = test_results.get('database', {})
        missing_indexes = db_test.get('metrics', {}).get('missing_indexes', 0)
        if missing_indexes > 0:
            recommendations.append(f"Consider creating {missing_indexes} recommended database indexes")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Performance optimization system is working well!")
        
        return recommendations
    
    def print_final_report(self, results: Dict[str, Any]):
        """Print comprehensive final test report."""
        print("\n" + "=" * 60)
        print("FINAL TEST REPORT")
        print("=" * 60)
        
        summary = results['summary']
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Success Rate: {summary['success_rate']}% ({summary['passed']}/{summary['total_tests']} tests passed)")
        
        print(f"\nPerformance Metrics:")
        metrics = summary['performance_metrics']
        print(f"  Average Response Time: {metrics['avg_response_time']}ms")
        print(f"  Cache Hit Rate: {metrics['cache_hit_rate']}%")
        print(f"  Memory Usage: {metrics['memory_usage_mb']}MB")
        
        print(f"\nRecommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print(f"\nDetailed Results:")
        for test_name, test_result in results['tests'].items():
            print(f"\n{test_name.upper()}:")
            for detail in test_result.get('details', []):
                print(f"  {detail}")


def main():
    """Main test execution function."""
    print("TaskMaster Performance Optimization Test Suite")
    print("Waiting for Flask application to be ready...")
    
    # Wait for application to be ready
    runner = PerformanceTestRunner()
    max_retries = 10
    
    for attempt in range(max_retries):
        try:
            response = runner.session.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("[CHECK] Flask application is ready")
                break
        except:
            if attempt < max_retries - 1:
                print(f"  Waiting for application... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                print("[X] Flask application not responding. Please start the Flask app first.")
                return False
    
    # Run tests
    results = runner.run_all_tests()
    
    # Save results to file
    results_file = f"performance_test_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest results saved to: {results_file}")
    
    return results['summary']['overall_status'] == 'PASS'


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)