"""
Schedule API Routes

Handles scheduling-related endpoints including task queue management,
time pools, and schedule generation functionality.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from models import db, TimePool, TaskAssignment, Task, WeatherForecast
from task_queue_service import get_task_queue_service
from weather_service import get_flask_weather_service
from assignment_service import get_assignment_service
import logging

logger = logging.getLogger(__name__)
schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/task-queue/all')
def get_all_tasks_queue():
    """Get all tasks ordered by priority score"""
    limit = int(request.args.get('limit', 100))
    
    try:
        queue_service = get_task_queue_service()
        task_queue = queue_service.get_all_tasks_queue(limit)
        
        return jsonify({
            'task_queue': task_queue,
            'task_queue_detailed': task_queue,  # For backward compatibility
            'count': len(task_queue)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'task_queue': [],
            'count': 0
        }), 500


@schedule_bp.route('/task-queue/available')
def get_available_tasks_queue():
    """Get available (unassigned/partially assigned) tasks ordered by priority"""
    limit = int(request.args.get('limit', 100))
    
    try:
        queue_service = get_task_queue_service()
        available_queue = queue_service.get_available_tasks_queue(limit)
        
        return jsonify({
            'available_tasks': available_queue,
            'available_tasks_detailed': available_queue,  # For backward compatibility
            'count': len(available_queue)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'available_tasks': [],
            'count': 0
        }), 500


@schedule_bp.route('/task-queue/statistics')
def get_queue_statistics():
    """Get task queue statistics"""
    try:
        queue_service = get_task_queue_service()
        stats = queue_service.get_queue_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@schedule_bp.route('/time-pools/regenerate', methods=['POST'])
def regenerate_time_pools():
    """Manually trigger time pool regeneration"""
    try:
        from background_service import background_service
        if background_service and background_service.is_running:
            background_service.regenerate_time_pools()
            return jsonify({'status': 'success', 'message': 'Time pool regeneration scheduled'})
        else:
            # If background service isn't running, regenerate directly
            pools_created, pools_updated = background_service.regenerate_all_time_pools(max_days_ahead=30)
            return jsonify({
                'status': 'success', 
                'message': 'Time pools regenerated directly',
                'pools_created': pools_created,
                'pools_updated': pools_updated
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@schedule_bp.route('/debug/task-queue', methods=['GET'])
def debug_task_queue():
    """Debug endpoint to check task queue filtering"""
    try:
        queue_service = get_task_queue_service()
        
        all_tasks = queue_service.get_all_tasks_queue(limit=10)
        available_tasks = queue_service.get_available_tasks_queue(limit=10)
        
        debug_info = {
            'all_tasks_count': len(all_tasks),
            'available_tasks_count': len(available_tasks),
            'all_tasks': [
                {
                    'title': task.get('title'),
                    'status': task.get('status'),
                    'can_be_scheduled': task.get('can_be_scheduled'),
                    'blocking_reasons': task.get('blocking_reasons'),
                    'is_assigned': task.get('is_assigned'),
                    'is_fully_assigned': task.get('is_fully_assigned'),
                    'remaining_minutes': task.get('remaining_minutes'),
                    'priority_score': task.get('priority_score')
                }
                for task in all_tasks
            ],
            'available_tasks': [
                {
                    'title': task.get('title'),
                    'can_be_scheduled': task.get('can_be_scheduled'),
                    'is_fully_assigned': task.get('is_fully_assigned'),
                    'priority_score': task.get('priority_score')
                }
                for task in available_tasks
            ]
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/time-pools', methods=['GET'])
def get_time_pools():
    """Get time pools with optional date filtering and weather data"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        include_weather = request.args.get('include_weather', 'false').lower() == 'true'
        
        # Base query for TimePool
        query = TimePool.query
        
        # Apply date filters
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(TimePool.pool_date >= start_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(TimePool.pool_date <= end_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        # Order by date and start time
        pools = query.order_by(TimePool.pool_date, TimePool.start_time).all()
        
        # Convert to dictionaries
        pools_data = []
        total_minutes = 0
        outdoor_suitable_count = 0
        
        # Get weather service if needed
        weather_service = get_flask_weather_service() if include_weather else None
        
        for pool in pools:
            pool_dict = pool.to_dict()
            
            # Add assignment information
            try:
                # Query task assignments for this pool
                assignments = TaskAssignment.query.filter_by(time_pool_id=pool.id).all()
                pool_dict['assignments'] = []
                allocated_minutes = 0
                
                for assignment in assignments:
                    # Get the task details
                    task = Task.query.get(assignment.task_id)
                    if task:
                        task_info = {
                            'task_id': assignment.task_id,
                            'task_title': task.title,
                            'allocated_minutes': assignment.allocated_minutes,
                            'status': assignment.status,
                            'urgency': task.urgency,
                            'priority': task.priority
                        }
                        pool_dict['assignments'].append(task_info)
                        allocated_minutes += assignment.allocated_minutes or 0
                
                # Calculate utilization
                pool_dict['allocated_minutes'] = allocated_minutes
                pool_dict['available_minutes'] = max(0, (pool.total_minutes or 0) - allocated_minutes)
                
            except Exception as e:
                logger.warning(f"Error getting assignments for pool {pool.id}: {e}")
                pool_dict['assignments'] = []
                pool_dict['allocated_minutes'] = 0
                pool_dict['available_minutes'] = pool.total_minutes or 0
            
            # Add weather information if requested
            if include_weather and weather_service:
                try:
                    weather_forecast = weather_service.get_by_date(pool.pool_date)
                    if weather_forecast:
                        weather_data = {
                            'weather_condition': weather_forecast.weather_condition,
                            'temp_high': weather_forecast.temp_high,
                            'temp_low': weather_forecast.temp_low,
                            'precipitation_probability': weather_forecast.precipitation_probability,
                            'suitable_for_outdoor_work': weather_forecast.is_suitable_for_outdoor_work()
                        }
                        pool_dict['weather'] = weather_data
                        
                        if weather_forecast.is_suitable_for_outdoor_work():
                            outdoor_suitable_count += 1
                    else:
                        pool_dict['weather'] = {
                            'weather_condition': 'Unknown',
                            'suitable_for_outdoor_work': False
                        }
                except Exception as e:
                    logger.warning(f"Error getting weather for pool {pool.id}: {e}")
                    pool_dict['weather'] = {
                        'weather_condition': 'Unknown',
                        'suitable_for_outdoor_work': False
                    }
            
            pools_data.append(pool_dict)
            total_minutes += pool.total_minutes or 0
        
        return jsonify({
            'pools': pools_data,
            'total_minutes': total_minutes,
            'pool_count': len(pools_data),
            'outdoor_suitable': outdoor_suitable_count if include_weather else None
        })
        
    except Exception as e:
        logger.error(f"Error retrieving time pools: {e}")
        return jsonify({
            'error': f"Failed to retrieve time pools: {str(e)}",
            'pools': [],
            'total_minutes': 0,
            'pool_count': 0
        }), 500