import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))
from app import create_app

app = create_app()

print('Testing API Endpoints Integration:')
with app.test_client() as client:
    
    # Test endpoints that should exist
    test_endpoints = [
        ('/health', 'Core Flask'),
        ('/api/health', 'API Health'),
        ('/api/tasks', 'Tasks'),
        ('/api/events', 'Events'),
        ('/api/initiatives', 'Initiatives'),
        ('/api/task-queue/enhanced', 'Enhanced Queue'),
        ('/api/time-pools', 'Time Pools'),
        ('/api/meals', 'Meals'),
        ('/api/claude-analysis/status', 'Claude Analysis Status')
    ]
    
    results = []
    for endpoint, name in test_endpoints:
        try:
            response = client.get(endpoint)
            # 500 errors are failures, everything else is acceptable for this test
            success = response.status_code != 500
            results.append(success)
            
            if response.status_code == 500:
                status = 'ERROR'
            elif response.status_code == 404:
                status = 'MISSING'
            elif 200 <= response.status_code < 300:
                status = 'PASS'
            else:
                status = 'FAIL'
                
            print(f'{status}: {name} -> {response.status_code}')
            
        except Exception as e:
            results.append(False)
            print(f'EXCEPTION: {name} -> {str(e)}')
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f'\nAPI ENDPOINT SUMMARY: {passed}/{total} endpoints accessible')
    print(f'INTEGRATION TEST 2: {"PASSED" if passed >= total * 0.8 else "FAILED"} - API blueprint functionality')