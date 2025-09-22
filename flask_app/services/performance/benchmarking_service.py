"""
Benchmarking Service

Comprehensive benchmarking and load testing capabilities for measuring
API performance before and after optimizations.

Features:
- API endpoint load testing
- Performance regression testing
- Before/after optimization comparisons
- Stress testing capabilities
- Performance reporting
- Automated benchmark scheduling
"""

import time
import asyncio
import statistics
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import json

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests."""
    base_url: str = 'http://localhost:5000'
    concurrent_users: int = 10
    requests_per_user: int = 20
    ramp_up_time: int = 5  # seconds
    timeout: int = 30
    retry_attempts: int = 3
    warm_up_requests: int = 5


@dataclass
class RequestResult:
    """Result of a single HTTP request."""
    url: str
    method: str
    status_code: int
    response_time: float
    response_size: int
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'method': self.method,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'response_size': self.response_size,
            'success': self.success,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class BenchmarkResult:
    """Results of a benchmark test."""
    test_name: str
    config: BenchmarkConfig
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_response_time: float
    min_response_time: float
    max_response_time: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    total_data_transferred: int
    detailed_results: List[RequestResult] = field(default_factory=list)
    errors: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'config': {
                'base_url': self.config.base_url,
                'concurrent_users': self.config.concurrent_users,
                'requests_per_user': self.config.requests_per_user,
                'ramp_up_time': self.config.ramp_up_time
            },
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': (self.end_time - self.start_time).total_seconds(),
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'avg_response_time': self.avg_response_time,
            'median_response_time': self.median_response_time,
            'min_response_time': self.min_response_time,
            'max_response_time': self.max_response_time,
            'p95_response_time': self.p95_response_time,
            'p99_response_time': self.p99_response_time,
            'requests_per_second': self.requests_per_second,
            'error_rate': self.error_rate,
            'total_data_transferred': self.total_data_transferred,
            'errors': self.errors
        }


class BenchmarkingService:
    """Main benchmarking and load testing service."""
    
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or BenchmarkConfig()
        self.benchmark_history: List[BenchmarkResult] = []
        self.session = self._create_session()
        
        # Standard test endpoints
        self.test_endpoints = {
            'health': {'path': '/health', 'method': 'GET'},
            'tasks_list': {'path': '/api/v2/tasks', 'method': 'GET'},
            'tasks_filtered': {'path': '/api/v2/tasks?status=active&limit=20', 'method': 'GET'},
            'events_list': {'path': '/api/v2/events', 'method': 'GET'},
            'events_calendar': {'path': '/api/v2/events/calendar?start=2025-09-19&end=2025-09-26', 'method': 'GET'},
            'schedule': {'path': '/api/schedule/queue', 'method': 'GET'},
            'assignments': {'path': '/api/assignments/suggestions', 'method': 'GET'}
        }
        
        logger.info("Benchmarking service initialized")
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=50)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def run_load_test(self, test_name: str, endpoints: Optional[List[str]] = None,
                     custom_config: Optional[BenchmarkConfig] = None) -> BenchmarkResult:
        """Run load test on specified endpoints."""
        config = custom_config or self.config
        endpoints = endpoints or list(self.test_endpoints.keys())
        
        logger.info(f"Starting load test: {test_name}")
        logger.info(f"Config: {config.concurrent_users} users, {config.requests_per_user} requests each")
        
        start_time = datetime.now()
        all_results: List[RequestResult] = []
        
        # Warm up
        self._warm_up(endpoints, config)
        
        # Run load test with thread pool
        with ThreadPoolExecutor(max_workers=config.concurrent_users) as executor:
            # Submit user simulation tasks
            futures = []
            for user_id in range(config.concurrent_users):
                # Stagger user start times for ramp-up
                delay = (config.ramp_up_time / config.concurrent_users) * user_id
                future = executor.submit(self._simulate_user, user_id, endpoints, config, delay)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    all_results.extend(user_results)
                except Exception as e:
                    logger.error(f"Error in user simulation: {e}")
        
        end_time = datetime.now()
        
        # Process results
        benchmark_result = self._process_results(test_name, config, start_time, end_time, all_results)
        
        # Store in history
        self.benchmark_history.append(benchmark_result)
        
        logger.info(f"Load test completed: {benchmark_result.avg_response_time:.2f}ms avg, "
                   f"{benchmark_result.requests_per_second:.2f} RPS, "
                   f"{benchmark_result.error_rate:.2f}% errors")
        
        return benchmark_result
    
    def _warm_up(self, endpoints: List[str], config: BenchmarkConfig):
        """Warm up the application with initial requests."""
        logger.info("Warming up application...")
        
        for endpoint_name in endpoints[:2]:  # Warm up first 2 endpoints
            endpoint = self.test_endpoints.get(endpoint_name)
            if endpoint:
                url = urljoin(config.base_url, endpoint['path'])
                try:
                    for _ in range(config.warm_up_requests):
                        self.session.request(endpoint['method'], url, timeout=config.timeout)
                        time.sleep(0.1)
                except Exception as e:
                    logger.warning(f"Warm-up request failed for {endpoint_name}: {e}")
    
    def _simulate_user(self, user_id: int, endpoints: List[str], 
                      config: BenchmarkConfig, delay: float) -> List[RequestResult]:
        """Simulate a single user making requests."""
        if delay > 0:
            time.sleep(delay)
        
        results = []
        
        for request_num in range(config.requests_per_user):
            # Cycle through endpoints
            endpoint_name = endpoints[request_num % len(endpoints)]
            endpoint = self.test_endpoints.get(endpoint_name)
            
            if not endpoint:
                continue
            
            url = urljoin(config.base_url, endpoint['path'])
            method = endpoint['method']
            
            # Make request and measure performance
            start_time = time.time()
            success = False
            status_code = 0
            response_size = 0
            error = None
            
            try:
                response = self.session.request(method, url, timeout=config.timeout)
                status_code = response.status_code
                response_size = len(response.content)
                success = 200 <= status_code < 400
                
                if not success:
                    error = f"HTTP {status_code}"
                    
            except requests.exceptions.Timeout:
                error = "Request timeout"
            except requests.exceptions.ConnectionError:
                error = "Connection error"
            except Exception as e:
                error = str(e)
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            result = RequestResult(
                url=url,
                method=method,
                status_code=status_code,
                response_time=response_time,
                response_size=response_size,
                success=success,
                error=error
            )
            
            results.append(result)
            
            # Small delay between requests from same user
            if request_num < config.requests_per_user - 1:
                time.sleep(0.1)
        
        return results
    
    def _process_results(self, test_name: str, config: BenchmarkConfig,
                        start_time: datetime, end_time: datetime,
                        results: List[RequestResult]) -> BenchmarkResult:
        """Process benchmark results and calculate statistics."""
        
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r.success)
        failed_requests = total_requests - successful_requests
        
        # Response time statistics
        response_times = [r.response_time for r in results if r.success]
        
        if response_times:
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            
            # Percentiles
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
            p99_response_time = sorted_times[min(p99_index, len(sorted_times) - 1)]
        else:
            min_response_time = max_response_time = avg_response_time = 0
            median_response_time = p95_response_time = p99_response_time = 0
        
        # Calculate requests per second
        duration = (end_time - start_time).total_seconds()
        requests_per_second = total_requests / duration if duration > 0 else 0
        
        # Error statistics
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        errors = {}
        for result in results:
            if result.error:
                errors[result.error] = errors.get(result.error, 0) + 1
        
        # Data transfer
        total_data_transferred = sum(r.response_size for r in results)
        
        return BenchmarkResult(
            test_name=test_name,
            config=config,
            start_time=start_time,
            end_time=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_response_time=sum(response_times),
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            total_data_transferred=total_data_transferred,
            detailed_results=results,
            errors=errors
        )
    
    def run_stress_test(self, test_name: str, max_users: int = 100, 
                       step_size: int = 10, step_duration: int = 30) -> List[BenchmarkResult]:
        """Run stress test with increasing load."""
        logger.info(f"Starting stress test: {test_name}")
        
        stress_results = []
        
        for users in range(step_size, max_users + 1, step_size):
            step_config = BenchmarkConfig(
                base_url=self.config.base_url,
                concurrent_users=users,
                requests_per_user=step_duration // 2,  # Approximate requests for duration
                ramp_up_time=5,
                timeout=self.config.timeout
            )
            
            step_name = f"{test_name}_stress_{users}users"
            result = self.run_load_test(step_name, custom_config=step_config)
            stress_results.append(result)
            
            logger.info(f"Stress test step {users} users: {result.avg_response_time:.2f}ms avg, "
                       f"{result.error_rate:.2f}% errors")
            
            # Stop if error rate is too high
            if result.error_rate > 50:
                logger.warning(f"High error rate detected ({result.error_rate:.2f}%), stopping stress test")
                break
            
            # Brief pause between steps
            time.sleep(2)
        
        return stress_results
    
    def compare_benchmarks(self, baseline_name: str, comparison_name: str) -> Dict[str, Any]:
        """Compare two benchmark results."""
        baseline = next((b for b in self.benchmark_history if b.test_name == baseline_name), None)
        comparison = next((b for b in self.benchmark_history if b.test_name == comparison_name), None)
        
        if not baseline or not comparison:
            return {'error': 'One or both benchmark results not found'}
        
        # Calculate improvements/regressions
        def calculate_change(baseline_val, comparison_val, inverse=False):
            if baseline_val == 0:
                return 0
            change = ((comparison_val - baseline_val) / baseline_val) * 100
            return -change if inverse else change
        
        comparison_result = {
            'baseline': baseline.to_dict(),
            'comparison': comparison.to_dict(),
            'improvements': {
                'avg_response_time': {
                    'baseline': baseline.avg_response_time,
                    'comparison': comparison.avg_response_time,
                    'change_percent': calculate_change(baseline.avg_response_time, comparison.avg_response_time, True),
                    'improvement': comparison.avg_response_time < baseline.avg_response_time
                },
                'requests_per_second': {
                    'baseline': baseline.requests_per_second,
                    'comparison': comparison.requests_per_second,
                    'change_percent': calculate_change(baseline.requests_per_second, comparison.requests_per_second),
                    'improvement': comparison.requests_per_second > baseline.requests_per_second
                },
                'error_rate': {
                    'baseline': baseline.error_rate,
                    'comparison': comparison.error_rate,
                    'change_percent': calculate_change(baseline.error_rate, comparison.error_rate, True),
                    'improvement': comparison.error_rate < baseline.error_rate
                },
                'p95_response_time': {
                    'baseline': baseline.p95_response_time,
                    'comparison': comparison.p95_response_time,
                    'change_percent': calculate_change(baseline.p95_response_time, comparison.p95_response_time, True),
                    'improvement': comparison.p95_response_time < baseline.p95_response_time
                }
            }
        }
        
        # Overall assessment
        improvements_count = sum(1 for metric in comparison_result['improvements'].values() if metric['improvement'])
        total_metrics = len(comparison_result['improvements'])
        
        comparison_result['overall_assessment'] = {
            'improved_metrics': improvements_count,
            'total_metrics': total_metrics,
            'improvement_rate': (improvements_count / total_metrics) * 100,
            'recommendation': 'Performance improved' if improvements_count >= total_metrics * 0.75 else 
                            'Mixed results' if improvements_count >= total_metrics * 0.5 else 
                            'Performance degraded'
        }
        
        return comparison_result
    
    def get_benchmark_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get benchmark history."""
        history = sorted(self.benchmark_history, key=lambda x: x.start_time, reverse=True)
        if limit:
            history = history[:limit]
        return [b.to_dict() for b in history]
    
    def export_results(self, test_name: str, format: str = 'json') -> Optional[str]:
        """Export benchmark results in specified format."""
        result = next((b for b in self.benchmark_history if b.test_name == test_name), None)
        
        if not result:
            return None
        
        if format.lower() == 'json':
            return json.dumps(result.to_dict(), indent=2)
        
        # Could add CSV, HTML formats in the future
        return None
    
    def clear_history(self):
        """Clear benchmark history."""
        self.benchmark_history.clear()
        logger.info("Benchmark history cleared")


# Global benchmarking service instance
benchmark_manager: Optional[BenchmarkingService] = None


def init_benchmarking_service(config: Optional[BenchmarkConfig] = None):
    """Initialize benchmarking service."""
    global benchmark_manager
    
    benchmark_manager = BenchmarkingService(config)
    
    return benchmark_manager