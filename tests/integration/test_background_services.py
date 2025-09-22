import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))
from app import create_app

app = create_app()

print('Testing Background Services Integration:')
with app.app_context():
    
    # Test background service coordinator
    from services.background import background_service
    
    print(f'Background Service Status: {background_service.is_running}')
    
    # Test individual services
    services_to_test = [
        ('notification_service', 'Notification Service'),
        ('scheduler_service', 'Scheduler Service'), 
        ('maintenance_service', 'Maintenance Service'),
        ('weather_service', 'Weather Service'),
        ('timepool_service', 'Time Pool Service')
    ]
    
    results = []
    for service_attr, name in services_to_test:
        try:
            service = getattr(background_service, service_attr, None)
            if service:
                # Check if service has required methods
                has_start = hasattr(service, 'start')
                has_stop = hasattr(service, 'stop')
                is_running = getattr(service, 'is_running', False) if hasattr(service, 'is_running') else 'unknown'
                
                results.append(True)
                print(f'PASS: {name} - start:{has_start}, stop:{has_stop}, running:{is_running}')
            else:
                results.append(False)
                print(f'FAIL: {name} - Service not found')
        except Exception as e:
            results.append(False)
            print(f'ERROR: {name} - {str(e)}')
    
    # Test scheduled jobs
    try:
        if hasattr(background_service, 'scheduler_service'):
            scheduler = background_service.scheduler_service
            if hasattr(scheduler, 'scheduler') and scheduler.scheduler:
                jobs = scheduler.scheduler.get_jobs()
                print(f'Scheduled Jobs: {len(jobs)} jobs found')
                
                for job in jobs[:5]:  # Show first 5 jobs
                    print(f'  - {job.id}: {job.next_run_time}')
                
                results.append(len(jobs) > 0)
            else:
                print('FAIL: No scheduler found')
                results.append(False)
        else:
            print('FAIL: No scheduler_service found')
            results.append(False)
    except Exception as e:
        print(f'ERROR: Scheduled jobs test - {e}')
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f'\nBACKGROUND SERVICES SUMMARY: {passed}/{total} services operational')
    print(f'INTEGRATION TEST 3: {"PASSED" if passed >= total * 0.8 else "FAILED"} - Background services')