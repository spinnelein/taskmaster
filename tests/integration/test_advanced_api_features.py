#!/usr/bin/env python3
"""
Advanced API Features Test Suite

Comprehensive test suite for validating the Advanced API Features
implementation including search, export, webhooks, and analytics.
"""
import requests
import json
import time
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List


class AdvancedAPITester:
    """Test suite for Advanced API Features"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.test_results = []
        self.api_key = None
        
        # Test data
        self.test_search_queries = [
            "high priority tasks",
            "project meeting",
            "type:task status:active",
            "urgent deadline"
        ]
        
        self.test_webhook_url = "https://httpbin.org/post"  # Test webhook endpoint
    
    def log(self, message: str, level: str = "INFO"):
        """Log test message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None, expected_status: int = 200) -> Dict:
        """Make test request and validate response"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Validate status code
            if response.status_code != expected_status:
                self.log(f"Unexpected status {response.status_code} for {method} {endpoint}", "WARNING")
            
            # Parse JSON response
            try:
                return response.json()
            except:
                return {'status_code': response.status_code, 'text': response.text}
                
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            return {'error': str(e)}
    
    def test_search_functionality(self):
        """Test comprehensive search features"""
        self.log("Testing Search Functionality")
        
        # Test 1: Basic search health check
        result = self.test_request('GET', '/api/search/health')
        if result.get('success'):
            self.log("[CHECK] Search service health check passed")
            self.test_results.append(('search_health', True, 'Search service is healthy'))
        else:
            self.log("[X] Search service health check failed", "ERROR")
            self.test_results.append(('search_health', False, 'Search service unhealthy'))
            return
        
        # Test 2: Initialize FTS indexes
        self.log("Initializing search indexes...")
        result = self.test_request('POST', '/api/search/index/rebuild')
        if result.get('success'):
            self.log("[CHECK] Search indexes initialized")
            self.test_results.append(('search_indexes', True, 'FTS indexes created'))
        else:
            self.log("[X] Search index initialization failed", "WARNING")
            self.test_results.append(('search_indexes', False, 'FTS initialization failed'))
        
        # Test 3: Basic search queries
        for query in self.test_search_queries:
            self.log(f"Testing search query: '{query}'")
            result = self.test_request('GET', f'/api/search/search?q={query}&limit=10')
            
            if result.get('success'):
                data = result.get('data', {})
                result_count = data.get('total_count', 0)
                query_time = data.get('query_time_ms', 0)
                
                self.log(f"[CHECK] Search '{query}': {result_count} results in {query_time}ms")
                self.test_results.append(('search_query', True, f"Query '{query}' returned {result_count} results"))
            else:
                self.log(f"[X] Search query '{query}' failed", "ERROR")
                self.test_results.append(('search_query', False, f"Query '{query}' failed"))
        
        # Test 4: Search suggestions
        self.log("Testing search suggestions")
        result = self.test_request('GET', '/api/search/suggestions?q=tas&limit=5')
        if result.get('success'):
            suggestions = result.get('data', {}).get('suggestions', [])
            self.log(f"[CHECK] Search suggestions: {len(suggestions)} suggestions")
            self.test_results.append(('search_suggestions', True, f"Got {len(suggestions)} suggestions"))
        else:
            self.log("[X] Search suggestions failed", "ERROR")
            self.test_results.append(('search_suggestions', False, 'Suggestions API failed'))
        
        # Test 5: Faceted search
        self.log("Testing faceted search")
        result = self.test_request('GET', '/api/search/search?q=task&include_facets=true')
        if result.get('success'):
            facets = result.get('data', {}).get('facets', {})
            facet_count = len(facets)
            self.log(f"[CHECK] Faceted search: {facet_count} facet categories")
            self.test_results.append(('search_facets', True, f"Got {facet_count} facet categories"))
        else:
            self.log("[X] Faceted search failed", "ERROR")
            self.test_results.append(('search_facets', False, 'Faceted search failed'))
        
        # Test 6: Saved searches
        self.log("Testing saved searches")
        saved_search_data = {
            'name': f'Test Search {uuid.uuid4().hex[:8]}',
            'query': 'high priority tasks',
            'description': 'Test saved search',
            'entity_types': ['tasks'],
            'category': 'test'
        }
        
        result = self.test_request('POST', '/api/search/saved', saved_search_data)
        if result.get('success'):
            saved_search_id = result.get('data', {}).get('id')
            self.log(f"[CHECK] Created saved search: {saved_search_id}")
            self.test_results.append(('saved_search_create', True, 'Saved search created'))
            
            # Test executing saved search
            if saved_search_id:
                result = self.test_request('GET', f'/api/search/saved/{saved_search_id}/execute')
                if result.get('success'):
                    self.log("[CHECK] Executed saved search")
                    self.test_results.append(('saved_search_execute', True, 'Saved search executed'))
                else:
                    self.log("[X] Failed to execute saved search", "ERROR")
                    self.test_results.append(('saved_search_execute', False, 'Execute failed'))
        else:
            self.log("[X] Failed to create saved search", "ERROR")
            self.test_results.append(('saved_search_create', False, 'Creation failed'))
    
    def test_export_functionality(self):
        """Test export features"""
        self.log("Testing Export Functionality")
        
        # Test 1: Export service health
        result = self.test_request('GET', '/api/export/health')
        if result.get('success'):
            self.log("[CHECK] Export service health check passed")
            self.test_results.append(('export_health', True, 'Export service healthy'))
        else:
            self.log("[X] Export service health check failed", "ERROR")
            self.test_results.append(('export_health', False, 'Export service unhealthy'))
            return
        
        # Test 2: Get supported formats
        result = self.test_request('GET', '/api/export/formats')
        if result.get('success'):
            formats = result.get('data', {}).get('formats', [])
            implemented_formats = [f for f in formats if f.get('implemented')]
            self.log(f"[CHECK] Export formats: {len(implemented_formats)} implemented")
            self.test_results.append(('export_formats', True, f"{len(implemented_formats)} formats available"))
        else:
            self.log("[X] Failed to get export formats", "ERROR")
            self.test_results.append(('export_formats', False, 'Formats API failed'))
        
        # Test 3: Create export requests for different formats
        test_formats = ['json', 'csv', 'ical']
        
        for format_type in test_formats:
            self.log(f"Testing {format_type.upper()} export")
            
            export_data = {
                'format': format_type,
                'entity_types': ['tasks', 'events'],
                'filters': {},
                'date_range': {
                    'start_date': '2024-01-01T00:00:00Z',
                    'end_date': '2024-12-31T23:59:59Z'
                }
            }
            
            result = self.test_request('POST', '/api/export/create', export_data)
            if result.get('success'):
                export_id = result.get('data', {}).get('export_id')
                self.log(f"[CHECK] Created {format_type} export: {export_id}")
                self.test_results.append((f'export_{format_type}', True, f"{format_type} export created"))
                
                # Check export status
                if export_id:
                    time.sleep(1)  # Brief wait for processing
                    status_result = self.test_request('GET', f'/api/export/{export_id}/status')
                    if status_result.get('success'):
                        status = status_result.get('data', {}).get('status')
                        self.log(f"[CHECK] Export {export_id} status: {status}")
                        self.test_results.append((f'export_{format_type}_status', True, f"Status: {status}"))
                    else:
                        self.log(f"[X] Failed to get export status", "WARNING")
                        self.test_results.append((f'export_{format_type}_status', False, 'Status check failed'))
            else:
                self.log(f"[X] Failed to create {format_type} export", "ERROR")
                self.test_results.append((f'export_{format_type}', False, f"{format_type} export failed"))
        
        # Test 4: Get active exports
        result = self.test_request('GET', '/api/export/active')
        if result.get('success'):
            exports = result.get('data', {}).get('exports', [])
            self.log(f"[CHECK] Active exports: {len(exports)}")
            self.test_results.append(('export_active', True, f"{len(exports)} active exports"))
        else:
            self.log("[X] Failed to get active exports", "ERROR")
            self.test_results.append(('export_active', False, 'Active exports API failed'))
    
    def test_webhook_functionality(self):
        """Test webhook features"""
        self.log("Testing Webhook Functionality")
        
        # Test 1: Webhook service health
        result = self.test_request('GET', '/api/webhooks/health')
        if result.get('success'):
            self.log("[CHECK] Webhook service health check passed")
            self.test_results.append(('webhook_health', True, 'Webhook service healthy'))
        else:
            self.log("[X] Webhook service health check failed", "ERROR")
            self.test_results.append(('webhook_health', False, 'Webhook service unhealthy'))
            return
        
        # Test 2: Get webhook events
        result = self.test_request('GET', '/api/webhooks/events')
        if result.get('success'):
            events = result.get('data', {}).get('events', [])
            self.log(f"[CHECK] Webhook events: {len(events)} available")
            self.test_results.append(('webhook_events', True, f"{len(events)} events available"))
        else:
            self.log("[X] Failed to get webhook events", "ERROR")
            self.test_results.append(('webhook_events', False, 'Events API failed'))
        
        # Test 3: Create webhook subscription
        webhook_data = {
            'name': f'Test Webhook {uuid.uuid4().hex[:8]}',
            'url': self.test_webhook_url,
            'description': 'Test webhook subscription',
            'events': ['task.created', 'task.updated'],
            'retry_count': 3,
            'timeout_seconds': 30
        }
        
        result = self.test_request('POST', '/api/webhooks/subscriptions', webhook_data)
        if result.get('success'):
            webhook_id = result.get('data', {}).get('id')
            self.log(f"[CHECK] Created webhook subscription: {webhook_id}")
            self.test_results.append(('webhook_create', True, 'Webhook subscription created'))
            
            # Test 4: Test webhook connectivity
            if webhook_id:
                self.log("Testing webhook connectivity...")
                test_result = self.test_request('POST', f'/api/webhooks/subscriptions/{webhook_id}/test')
                if test_result.get('success'):
                    test_successful = test_result.get('data', {}).get('test_successful')
                    status_code = test_result.get('data', {}).get('status_code')
                    self.log(f"[CHECK] Webhook test: {test_successful} (status: {status_code})")
                    self.test_results.append(('webhook_test', test_successful, f"Test result: {status_code}"))
                else:
                    self.log("[X] Webhook test failed", "ERROR")
                    self.test_results.append(('webhook_test', False, 'Test request failed'))
                
                # Test 5: Get webhook analytics
                analytics_result = self.test_request('GET', f'/api/webhooks/subscriptions/{webhook_id}/analytics')
                if analytics_result.get('success'):
                    analytics = analytics_result.get('data', {})
                    total_deliveries = analytics.get('total_deliveries', 0)
                    self.log(f"[CHECK] Webhook analytics: {total_deliveries} deliveries")
                    self.test_results.append(('webhook_analytics', True, f"{total_deliveries} deliveries"))
                else:
                    self.log("[X] Failed to get webhook analytics", "WARNING")
                    self.test_results.append(('webhook_analytics', False, 'Analytics failed'))
        else:
            self.log("[X] Failed to create webhook subscription", "ERROR")
            self.test_results.append(('webhook_create', False, 'Creation failed'))
        
        # Test 6: Get webhook subscriptions
        result = self.test_request('GET', '/api/webhooks/subscriptions')
        if result.get('success'):
            subscriptions = result.get('data', {}).get('subscriptions', [])
            self.log(f"[CHECK] Webhook subscriptions: {len(subscriptions)}")
            self.test_results.append(('webhook_list', True, f"{len(subscriptions)} subscriptions"))
        else:
            self.log("[X] Failed to get webhook subscriptions", "ERROR")
            self.test_results.append(('webhook_list', False, 'List API failed'))
    
    def test_analytics_functionality(self):
        """Test analytics and API key features"""
        self.log("Testing Analytics Functionality")
        
        # Test 1: Analytics service health (without API key first)
        result = self.test_request('GET', '/api/analytics/health')
        if result.get('success'):
            self.log("[CHECK] Analytics service health check passed")
            self.test_results.append(('analytics_health', True, 'Analytics service healthy'))
        else:
            self.log("[X] Analytics service health check failed", "ERROR")
            self.test_results.append(('analytics_health', False, 'Analytics service unhealthy'))
        
        # Note: Full analytics testing would require admin API key
        # For this basic test, we'll just verify the endpoints are accessible
        
        # Test 2: Rate limit status (without auth)
        result = self.test_request('GET', '/api/analytics/rate-limits', expected_status=401)
        if result.get('code') == 'MISSING_API_KEY':
            self.log("[CHECK] Rate limiting properly requires API key")
            self.test_results.append(('analytics_auth', True, 'API key authentication required'))
        else:
            self.log("[X] Rate limiting auth check unexpected", "WARNING")
            self.test_results.append(('analytics_auth', False, 'Auth behavior unexpected'))
        
        # Test 3: API key endpoints (should require admin)
        result = self.test_request('GET', '/api/analytics/api-keys', expected_status=401)
        if result.get('code') == 'MISSING_API_KEY':
            self.log("[CHECK] API key management properly secured")
            self.test_results.append(('analytics_security', True, 'Admin endpoints secured'))
        else:
            self.log("[X] API key management security issue", "WARNING")
            self.test_results.append(('analytics_security', False, 'Security issue detected'))
    
    def test_integration_features(self):
        """Test integration between different features"""
        self.log("Testing Integration Features")
        
        # Test 1: Search with export
        self.log("Testing search + export integration")
        
        # First do a search
        search_result = self.test_request('GET', '/api/search/search?q=task&limit=5')
        if search_result.get('success'):
            search_count = search_result.get('data', {}).get('total_count', 0)
            
            # Then export similar data
            export_data = {
                'format': 'json',
                'entity_types': ['tasks'],
                'filters': {}
            }
            
            export_result = self.test_request('POST', '/api/export/create', export_data)
            if export_result.get('success'):
                self.log("[CHECK] Search + Export integration working")
                self.test_results.append(('integration_search_export', True, 'Search and export integration'))
            else:
                self.log("[X] Export after search failed", "ERROR")
                self.test_results.append(('integration_search_export', False, 'Export integration failed'))
        else:
            self.log("[X] Search for integration test failed", "ERROR")
            self.test_results.append(('integration_search_export', False, 'Search integration failed'))
        
        # Test 2: Overall API structure
        self.log("Testing overall API structure")
        
        # Check all main endpoints are accessible
        endpoints_to_check = [
            '/api/search/health',
            '/api/export/health', 
            '/api/webhooks/health',
            '/api/analytics/health'
        ]
        
        accessible_endpoints = 0
        for endpoint in endpoints_to_check:
            result = self.test_request('GET', endpoint)
            if result.get('success'):
                accessible_endpoints += 1
        
        if accessible_endpoints == len(endpoints_to_check):
            self.log("[CHECK] All advanced API endpoints accessible")
            self.test_results.append(('integration_endpoints', True, 'All endpoints accessible'))
        else:
            self.log(f"[X] Only {accessible_endpoints}/{len(endpoints_to_check)} endpoints accessible", "WARNING")
            self.test_results.append(('integration_endpoints', False, f"Only {accessible_endpoints} endpoints working"))
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        self.log("=== Starting Advanced API Features Test Suite ===")
        start_time = time.time()
        
        try:
            # Test core server availability
            result = self.test_request('GET', '/health')
            if not result.get('success', False):
                self.log("ERROR: TaskMaster server not accessible", "ERROR")
                return False
            
            self.log("[CHECK] TaskMaster server is accessible")
            
            # Run all test suites
            self.test_search_functionality()
            self.test_export_functionality()
            self.test_webhook_functionality()
            self.test_analytics_functionality()
            self.test_integration_features()
            
        except Exception as e:
            self.log(f"Test suite failed with exception: {e}", "ERROR")
            return False
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r[1]])
        failed_tests = total_tests - passed_tests
        test_duration = time.time() - start_time
        
        # Print summary
        self.log("=== Test Suite Summary ===")
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {passed_tests}")
        self.log(f"Failed: {failed_tests}")
        self.log(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        self.log(f"Duration: {test_duration:.2f} seconds")
        
        if failed_tests > 0:
            self.log("\nFailed Tests:")
            for test_name, passed, message in self.test_results:
                if not passed:
                    self.log(f"  [X] {test_name}: {message}")
        
        self.log("\nPassed Tests:")
        for test_name, passed, message in self.test_results:
            if passed:
                self.log(f"  [CHECK] {test_name}: {message}")
        
        return failed_tests == 0


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Advanced API Features')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL for TaskMaster API (default: http://localhost:5000)')
    parser.add_argument('--verbose', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create and run tester
    tester = AdvancedAPITester(base_url=args.url)
    success = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()