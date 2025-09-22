"""
Shared utility functions for API routes
"""
from datetime import datetime, timedelta
from assignment_service import get_assignment_service
import logging

logger = logging.getLogger(__name__)


def trigger_pool_regeneration():
    """Trigger time pool regeneration when events change"""
    try:
        from services.background import background_service
        if background_service and background_service.is_running:
            background_service.regenerate_time_pools()
            logger.info("Time pool regeneration triggered successfully")
        else:
            logger.warning("Background service not running - pool regeneration skipped")
    except Exception as e:
        logger.error(f"Could not trigger pool regeneration: {e}")


def trigger_assignment_regeneration():
    """Trigger task assignment regeneration when tasks change"""
    try:
        from background_service import background_service
        if background_service and background_service.is_running:
            # Use a fixed job ID so we don't create multiple pending jobs
            job_id = 'task_change_assignment_regen'
            
            # Check if there's already a pending job
            existing_job = background_service.scheduler.get_job(job_id)
            if existing_job:
                # Remove existing job and create a new one with updated time
                background_service.scheduler.remove_job(job_id)
            
            # Schedule assignment regeneration with a small delay
            background_service.scheduler.add_job(
                func=background_service._regenerate_task_assignments,
                args=['task_change'],
                trigger='date',
                run_date=datetime.now() + timedelta(seconds=5),  # Reduced delay
                id=job_id,
                name='Task Change Assignment Regeneration',
                max_instances=1
            )
        else:
            # If background service isn't running, try direct assignment
            assignment_service = get_assignment_service()
            assignment_service.bulk_assign_tasks_to_pools(
                clear_existing=True,
                max_days_ahead=7,
                assigned_by='task_change_direct'
            )
    except Exception as e:
        print(f"Could not trigger assignment regeneration: {e}")


def parse_date_range(start_str, end_str):
    """Parse start and end date strings with fallback to current month"""
    from datetime import date
    
    if start_str and end_str:
        start_date = datetime.fromisoformat(start_str.replace('Z', '')).date()
        end_date = datetime.fromisoformat(end_str.replace('Z', '')).date()
    else:
        # Default to current month
        today = date.today()
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    return start_date, end_date


def parse_datetime_with_timezone(dt_string):
    """Parse datetime string with timezone handling"""
    if dt_string:
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    return None


def get_error_response(message, status_code=400):
    """Create standardized error response"""
    return {'error': message}, status_code


def get_success_response(data=None, message=None):
    """Create standardized success response"""
    response = {}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return response