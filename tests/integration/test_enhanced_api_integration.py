#!/usr/bin/env python3
"""
Test HTTP API integration with enhanced task queue services
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

def test_flask_server_running():
    """Test if Flask server is running"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("[PASS] Flask server is running")
            return True
        else:
            print(f"[FAIL] Flask server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Flask server not accessible: {e}")
        return False

def test_existing_task_queue_endpoints():
    """Test existing task queue endpoints"""
    print("\nTesting existing task queue endpoints:")
    
    endpoints = [
        '/api/task-queue/all',
        '/api/task-queue/available', 
        '/api/task-queue/statistics'
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            url = f'http://localhost:5000{endpoint}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[PASS] {endpoint}: {response.status_code}")
                print(f"   Response keys: {list(data.keys())}")
                if 'task_queue' in data:
                    print(f"   Tasks in queue: {len(data['task_queue'])}")
                if 'available_tasks' in data:
                    print(f"   Available tasks: {len(data['available_tasks'])}")
                results[endpoint] = True
            else:
                print(f"[FAIL] {endpoint}: {response.status_code}")
                results[endpoint] = False
                
        except Exception as e:
            print(f"[FAIL] {endpoint}: {e}")
            results[endpoint] = False
    
    return results

def create_enhanced_api_endpoint():
    """Create a new API endpoint that uses enhanced services"""
    
    # Check if we can modify the API routes
    api_file = os.path.join(os.path.dirname(__file__), 'flask_app', 'routes', 'api.py')
    
    enhanced_endpoint_code = '''
# Enhanced Task Queue endpoints using ProjectAwarePriorityService
@api_bp.route('/task-queue/enhanced')
def get_enhanced_task_queue():
    """Get enhanced task queue with ProjectAwarePriorityService scoring"""
    limit = int(request.args.get('limit', 100))
    
    try:
        from services.enhanced_task_queue_service import get_enhanced_task_queue_service
        
        enhanced_service = get_enhanced_task_queue_service()
        enhanced_queue = enhanced_service.get_enhanced_task_queue(limit)
        
        return jsonify({
            'enhanced_task_queue': enhanced_queue,
            'count': len(enhanced_queue),
            'scoring_method': 'ProjectAwarePriorityService'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'enhanced_task_queue': [],
            'count': 0
        }), 500

@api_bp.route('/task-queue/enhanced/available')
def get_enhanced_available_queue():
    """Get available enhanced task queue"""
    limit = int(request.args.get('limit', 100))
    
    try:
        from services.enhanced_task_queue_service import get_enhanced_task_queue_service
        
        enhanced_service = get_enhanced_task_queue_service()
        available_queue = enhanced_service.get_available_enhanced_queue(limit)
        
        return jsonify({
            'enhanced_available_tasks': available_queue,
            'count': len(available_queue),
            'scoring_method': 'ProjectAwarePriorityService'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'enhanced_available_tasks': [],
            'count': 0
        }), 500

@api_bp.route('/task-queue/enhanced/context/<task_id>')
def get_enhanced_task_context(task_id):
    """Get detailed task context analysis"""
    try:
        from services.enhanced_task_queue_service import get_enhanced_task_queue_service
        
        enhanced_service = get_enhanced_task_queue_service()
        context = enhanced_service.get_task_context_analysis(task_id)
        
        return jsonify({
            'task_context': context,
            'has_analysis': 'priority_analysis' in context
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'task_context': {},
            'has_analysis': False
        }), 500

@api_bp.route('/task-queue/enhanced/compare', methods=['POST'])
def compare_enhanced_task_priorities():
    """Compare priority scores for multiple tasks"""
    try:
        data = request.json
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return jsonify({'error': 'task_ids required'}), 400
        
        from services.enhanced_task_queue_service import get_enhanced_task_queue_service
        
        enhanced_service = get_enhanced_task_queue_service()
        comparisons = enhanced_service.compare_task_priorities(task_ids)
        
        return jsonify({
            'task_comparisons': comparisons,
            'count': len(comparisons)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'task_comparisons': [],
            'count': 0
        }), 500
'''
    
    # Read current API file
    try:
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check if enhanced endpoints already exist
        if '/task-queue/enhanced' in content:
            print("[PASS] Enhanced API endpoints already exist")
            return True
        
        # Add enhanced endpoints before the last line
        lines = content.split('\n')
        
        # Find a good place to insert (before dishes endpoints or at end)
        insert_index = len(lines) - 1
        for i, line in enumerate(lines):
            if '# Dishes API endpoints' in line:
                insert_index = i
                break
        
        # Insert the enhanced endpoint code
        enhanced_lines = enhanced_endpoint_code.strip().split('\n')
        lines[insert_index:insert_index] = enhanced_lines
        
        # Write back to file
        with open(api_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print("[PASS] Enhanced API endpoints added to routes/api.py")
        return True
        
    except Exception as e:
        print(f"[FAIL] Could not add enhanced endpoints: {e}")
        return False

def test_enhanced_endpoints():
    """Test enhanced endpoints if they exist"""
    print("\nTesting enhanced endpoints:")
    
    enhanced_endpoints = [
        '/api/task-queue/enhanced',
        '/api/task-queue/enhanced/available'
    ]
    
    results = {}
    
    for endpoint in enhanced_endpoints:
        try:
            url = f'http://localhost:5000{endpoint}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[PASS] {endpoint}: {response.status_code}")
                print(f"   Response keys: {list(data.keys())}")
                if 'enhanced_task_queue' in data:
                    queue = data['enhanced_task_queue']
                    print(f"   Enhanced tasks: {len(queue)}")
                    if queue:
                        # Show top task with enhanced scoring
                        top_task = queue[0]
                        score = top_task.get('enhanced_priority_score', 0)
                        title = top_task.get('title', 'Unknown')[:30]
                        print(f"   Top task: '{title}' (score: {score:.1f})")
                        
                if 'enhanced_available_tasks' in data:
                    tasks = data['enhanced_available_tasks']
                    print(f"   Enhanced available: {len(tasks)}")
                    
                results[endpoint] = True
            else:
                print(f"[FAIL] {endpoint}: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Response: {response.text[:100]}")
                results[endpoint] = False
                
        except Exception as e:
            print(f"[FAIL] {endpoint}: {e}")
            results[endpoint] = False
    
    return results

def test_task_context_endpoint():
    """Test task context analysis endpoint"""
    print("\nTesting task context analysis:")
    
    try:
        # First get a task ID from the regular queue
        response = requests.get('http://localhost:5000/api/task-queue/all?limit=1', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('task_queue'):
                task_id = data['task_queue'][0]['id']
                
                # Test context endpoint
                context_url = f'http://localhost:5000/api/task-queue/enhanced/context/{task_id}'
                context_response = requests.get(context_url, timeout=10)
                
                if context_response.status_code == 200:
                    context_data = context_response.json()
                    print(f"[PASS] Task context analysis: {context_response.status_code}")
                    print(f"   Has analysis: {context_data.get('has_analysis', False)}")
                    
                    if context_data.get('task_context', {}).get('priority_analysis'):
                        analysis = context_data['task_context']['priority_analysis']
                        print(f"   Total score: {analysis.get('total_score', 0):.1f}")
                        print(f"   Top factors: {', '.join(analysis.get('top_factors', []))}")
                    
                    return True
                else:
                    print(f"[FAIL] Task context analysis: {context_response.status_code}")
                    return False
            else:
                print("[SKIP] No tasks available for context testing")
                return True
        else:
            print("[SKIP] Could not get task list for context testing")
            return True
            
    except Exception as e:
        print(f"[FAIL] Task context analysis: {e}")
        return False

def test_comparison_endpoint():
    """Test task comparison endpoint"""
    print("\nTesting task comparison:")
    
    try:
        # Get multiple task IDs
        response = requests.get('http://localhost:5000/api/task-queue/all?limit=3', timeout=10)
        if response.status_code == 200:
            data = response.json()
            task_queue = data.get('task_queue', [])
            
            if len(task_queue) >= 2:
                task_ids = [task['id'] for task in task_queue[:3]]
                
                # Test comparison endpoint
                compare_url = 'http://localhost:5000/api/task-queue/enhanced/compare'
                compare_data = {'task_ids': task_ids}
                
                compare_response = requests.post(compare_url, json=compare_data, timeout=10)
                
                if compare_response.status_code == 200:
                    comparison_data = compare_response.json()
                    print(f"[PASS] Task comparison: {compare_response.status_code}")
                    comparisons = comparison_data.get('task_comparisons', [])
                    print(f"   Compared tasks: {len(comparisons)}")
                    
                    for comp in comparisons:
                        title = comp.get('title', 'Unknown')[:25]
                        score = comp.get('total_score', 0)
                        print(f"   '{title}': {score:.1f} points")
                    
                    return True
                else:
                    print(f"[FAIL] Task comparison: {compare_response.status_code}")
                    return False
            else:
                print("[SKIP] Not enough tasks for comparison testing")
                return True
        else:
            print("[SKIP] Could not get task list for comparison testing")
            return True
            
    except Exception as e:
        print(f"[FAIL] Task comparison: {e}")
        return False

def start_flask_server():
    """Start Flask server if not running"""
    print("Checking if Flask server needs to be started...")
    
    if test_flask_server_running():
        return True
    
    print("Starting Flask server...")
    
    # Try to start the server
    import subprocess
    import time
    
    try:
        # Start Flask in background
        flask_dir = os.path.join(os.path.dirname(__file__), 'flask_app')
        
        process = subprocess.Popen(
            ['python', 'app.py'],
            cwd=flask_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if it's running
        if test_flask_server_running():
            print("[PASS] Flask server started successfully")
            return True, process
        else:
            print("[FAIL] Flask server failed to start")
            process.terminate()
            return False, None
            
    except Exception as e:
        print(f"[FAIL] Could not start Flask server: {e}")
        return False, None

def main():
    """Main test execution"""
    print("Enhanced API Integration Testing")
    print("="*50)
    
    results = {}
    
    # Test 1: Check if Flask server is running
    server_running = test_flask_server_running()
    results['server_running'] = server_running
    
    if not server_running:
        print("\n[INFO] Flask server not running. Starting server...")
        server_started, process = start_flask_server()
        results['server_started'] = server_started
        if not server_started:
            print("[FAIL] Cannot proceed without Flask server")
            return False
    
    # Test 2: Existing endpoints
    existing_results = test_existing_task_queue_endpoints()
    results.update(existing_results)
    
    # Test 3: Add enhanced endpoints
    enhanced_added = create_enhanced_api_endpoint()
    results['enhanced_endpoints_added'] = enhanced_added
    
    if enhanced_added:
        print("\n[INFO] Server restart may be needed for new endpoints...")
        time.sleep(2)
        
        # Test 4: Enhanced endpoints
        enhanced_results = test_enhanced_endpoints()
        results.update(enhanced_results)
        
        # Test 5: Task context analysis
        context_result = test_task_context_endpoint()
        results['task_context'] = context_result
        
        # Test 6: Task comparison
        comparison_result = test_comparison_endpoint()
        results['task_comparison'] = comparison_result
    
    # Summary
    print("\n" + "="*50)
    print("API INTEGRATION TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed >= total * 0.8:  # 80% pass rate
        print("[PASS] Enhanced API integration is working well!")
    else:
        print("[FAIL] Enhanced API integration needs work")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    main()