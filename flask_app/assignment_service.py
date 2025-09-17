# assignment_service.py - Basic task-to-pool assignment service
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from models import db, Task, TimePool, TaskAssignment
from task_queue_service import get_task_queue_service
import uuid
import json

logger = logging.getLogger(__name__)

class FlaskAssignmentService:
    """Service for managing task assignments to time pools"""
    
    def __init__(self):
        self.queue_service = get_task_queue_service()
    
    def assign_task_to_pool(
        self, 
        task_id: str, 
        time_pool_id: str, 
        allocated_minutes: int,
        assigned_by: str = 'user',
        scheduled_start: Optional[datetime] = None,
        scheduled_end: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Assign a task to a time pool
        Returns: (success, message, assignment_dict)
        """
        try:
            # Validate task exists and can be assigned
            task = Task.query.get(task_id)
            if not task:
                return False, f"Task {task_id} not found", None
            
            if task.is_completed:
                return False, "Cannot assign completed task", None
            
            # Validate time pool exists and has capacity
            time_pool = TimePool.query.get(time_pool_id)
            if not time_pool:
                return False, f"Time pool {time_pool_id} not found", None
            
            if time_pool.available_minutes < allocated_minutes:
                return False, f"Time pool only has {time_pool.available_minutes} minutes available, requested {allocated_minutes}", None
            
            # Check if task has snoozed_until (start date) - pool must END after snooze time
            if task.snoozed_until:
                # Calculate pool end time
                if isinstance(time_pool.end_time, datetime):
                    pool_end_time = time_pool.end_time.time()
                else:
                    pool_end_time = time_pool.end_time
                
                pool_end_datetime = datetime.combine(time_pool.pool_date, pool_end_time)
                if pool_end_datetime <= task.snoozed_until:
                    start_time_str = task.snoozed_until.strftime('%Y-%m-%d %H:%M')
                    return False, f"Pool ends before task start time {start_time_str}", None
            
            # Check if task duration allows this allocation
            if task.duration:
                # Get existing assignments for this task
                existing_assignments = TaskAssignment.query.filter_by(
                    task_id=task_id
                ).filter(TaskAssignment.status.in_(['assigned', 'started'])).all()
                
                total_assigned = sum(a.allocated_minutes for a in existing_assignments)
                if total_assigned + allocated_minutes > task.duration:
                    return False, f"Assignment would exceed task duration. Task: {task.duration}min, Already assigned: {total_assigned}min, Requested: {allocated_minutes}min", None
            
            # Create the assignment
            assignment = TaskAssignment(
                id=str(uuid.uuid4()),
                task_id=task_id,
                time_pool_id=time_pool_id,
                allocated_minutes=allocated_minutes,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                assigned_at=datetime.utcnow(),
                assigned_by=assigned_by,
                notes=notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Update time pool allocation
            time_pool.allocated_minutes = (time_pool.allocated_minutes or 0) + allocated_minutes
            time_pool.available_minutes = time_pool.total_minutes - time_pool.allocated_minutes
            time_pool.updated_at = datetime.utcnow()
            
            db.session.add(assignment)
            db.session.commit()
            
            logger.info(f"Assigned task {task_id} ({allocated_minutes}min) to pool {time_pool_id}")
            return True, f"Task assigned {allocated_minutes} minutes in time pool", assignment.to_dict()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning task {task_id} to pool {time_pool_id}: {e}")
            return False, f"Assignment failed: {str(e)}", None
    
    def remove_assignment(self, assignment_id: str, reason: str = "Manual removal") -> Tuple[bool, str]:
        """
        Remove/cancel a task assignment
        Returns: (success, message)
        """
        try:
            assignment = TaskAssignment.query.get(assignment_id)
            if not assignment:
                return False, f"Assignment {assignment_id} not found"
            
            # Cancel the assignment (this also updates the time pool)
            assignment.cancel_assignment(reason)
            db.session.commit()
            
            logger.info(f"Cancelled assignment {assignment_id}: {reason}")
            return True, "Assignment cancelled successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling assignment {assignment_id}: {e}")
            return False, f"Failed to cancel assignment: {str(e)}"
    
    def get_assignments_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all assignments for a specific task"""
        try:
            assignments = TaskAssignment.get_assignments_for_task(task_id)
            return [a.to_dict() for a in assignments]
        except Exception as e:
            logger.error(f"Error getting assignments for task {task_id}: {e}")
            return []
    
    def get_assignments_for_pool(self, time_pool_id: str) -> List[Dict[str, Any]]:
        """Get all assignments for a specific time pool"""
        try:
            assignments = TaskAssignment.get_assignments_for_pool(time_pool_id)
            return [a.to_dict() for a in assignments]
        except Exception as e:
            logger.error(f"Error getting assignments for pool {time_pool_id}: {e}")
            return []
    
    def suggest_pools_for_task(self, task_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Suggest time pools that would be good matches for a task
        Returns pool suggestions with matching scores
        """
        try:
            task = Task.query.get(task_id)
            if not task:
                return []
            
            # Get available time pools
            today = date.today()
            end_date = today + timedelta(days=14)  # Look ahead 2 weeks
            
            # Get all available pools in date range
            available_pools = TimePool.query.filter(
                TimePool.pool_date >= today,
                TimePool.pool_date <= end_date,
                TimePool.available_minutes >= (task.duration or 30)
            ).order_by(TimePool.pool_date, TimePool.start_time).all()
            
            # Filter pools based on snoozed_until - pool must END after snooze time
            if task.snoozed_until:
                filtered_pools = []
                for pool in available_pools:
                    # Calculate pool end time
                    if isinstance(pool.end_time, datetime):
                        pool_end_time = pool.end_time.time()
                    else:
                        pool_end_time = pool.end_time
                    
                    pool_end_datetime = datetime.combine(pool.pool_date, pool_end_time)
                    if pool_end_datetime > task.snoozed_until:
                        filtered_pools.append(pool)
                available_pools = filtered_pools
            
            suggestions = []
            for pool in available_pools:
                score = self._calculate_pool_match_score(task.to_dict(), pool)
                
                suggestion = {
                    'pool': pool.to_dict(),
                    'match_score': score,
                    'can_fit_full_task': pool.available_minutes >= (task.duration or 0),
                    'reasons': self._get_match_reasons(task, pool, score)
                }
                suggestions.append(suggestion)
            
            # Sort by match score (descending)
            suggestions.sort(key=lambda x: x['match_score'], reverse=True)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error suggesting pools for task {task_id}: {e}")
            return []
    
    def suggest_tasks_for_pool(self, time_pool_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Suggest tasks that would be good matches for a time pool
        Returns task suggestions with matching scores
        """
        try:
            time_pool = TimePool.query.get(time_pool_id)
            if not time_pool:
                return []
            
            # Get available tasks from queue
            available_tasks = self.queue_service.get_available_tasks_queue(limit * 2)
            
            suggestions = []
            for task_item in available_tasks:
                task = task_item['task']
                remaining_minutes = task_item.get('remaining_minutes', task.duration or 0)
                
                # Skip if task won't fit
                if remaining_minutes > time_pool.available_minutes:
                    continue
                
                score = self._calculate_pool_match_score(task, time_pool)
                
                suggestion = {
                    'task': task_item['task_dict'],
                    'task_detailed': task_item,
                    'match_score': score,
                    'allocation_minutes': min(remaining_minutes, time_pool.available_minutes),
                    'would_complete_task': remaining_minutes <= time_pool.available_minutes,
                    'reasons': self._get_match_reasons(task, time_pool, score)
                }
                suggestions.append(suggestion)
            
            # Sort by match score (descending)
            suggestions.sort(key=lambda x: x['match_score'], reverse=True)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error suggesting tasks for pool {time_pool_id}: {e}")
            return []
    
    def _calculate_pool_match_score(self, task: Task, pool: TimePool) -> float:
        """Calculate how well a task matches a time pool (0-100)"""
        score = 50.0  # Base score
        
        try:
            # Due date proximity scoring
            if task.due_date and pool.pool_date:
                days_until_due = (task.due_date - pool.pool_date).days
                if days_until_due < 0:
                    score += 30  # Overdue tasks get high priority
                elif days_until_due == 0:
                    score += 25  # Due same day
                elif days_until_due <= 2:
                    score += 20  # Due soon
                elif days_until_due <= 7:
                    score += 10  # Due this week
                else:
                    score -= 5   # Due later
            
            # Weather matching
            weather = pool.get_weather_forecast()
            if weather and task.required_weather:
                try:
                    required_weather = json.loads(task.required_weather) if isinstance(task.required_weather, str) else task.required_weather
                    if required_weather:
                        outdoor_suitable = weather.is_suitable_for_outdoor_work()
                        if 'outdoor' in str(required_weather).lower() and outdoor_suitable:
                            score += 15
                        elif 'indoor' in str(required_weather).lower() and not outdoor_suitable:
                            score += 15
                except:
                    pass
            
            # Time of day preferences
            if pool.start_time:
                hour = pool.start_time.hour
                # Morning tasks (8-12)
                if 8 <= hour < 12:
                    score += 5  # Slight preference for morning productivity
                # Afternoon focus time (13-17)
                elif 13 <= hour < 17:
                    score += 3
                # Evening admin time (17-20)
                elif 17 <= hour < 20:
                    if task.duration and task.duration <= 60:  # Short tasks
                        score += 5
            
            # Context matching
            pool_context = pool.get_context_tags_list()
            if pool_context:
                if 'focus_time' in pool_context and task.urgency and task.urgency >= 7:
                    score += 10  # High urgency tasks in focus time
                if 'work_time' in pool_context and pool.is_work_time:
                    score += 5   # Work tasks in work time
            
            # Duration matching
            if task.duration and pool.available_minutes:
                if task.duration <= pool.available_minutes:
                    # Task fits completely
                    utilization = task.duration / pool.available_minutes
                    if 0.7 <= utilization <= 1.0:
                        score += 15  # Good utilization
                    elif 0.5 <= utilization < 0.7:
                        score += 10  # Decent utilization
                    elif utilization < 0.3:
                        score -= 5   # Poor utilization for small tasks
                else:
                    # Task needs to be split
                    score -= 10
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return 50.0
    
    def _get_match_reasons(self, task: Task, pool: TimePool, score: float) -> List[str]:
        """Get human-readable reasons for the match score"""
        reasons = []
        
        try:
            # Due date reasons
            if task.due_date and pool.pool_date:
                days_until_due = (task.due_date - pool.pool_date).days
                if days_until_due < 0:
                    reasons.append(f"OVERDUE by {abs(days_until_due)} days")
                elif days_until_due == 0:
                    reasons.append("Due TODAY")
                elif days_until_due <= 2:
                    reasons.append(f"Due in {days_until_due} days")
            
            # Weather reasons
            weather = pool.get_weather_forecast()
            if weather:
                if weather.is_suitable_for_outdoor_work():
                    reasons.append("Good weather for outdoor work")
                else:
                    reasons.append("Indoor weather conditions")
            
            # Time context reasons
            if pool.start_time:
                hour = pool.start_time.hour
                if 8 <= hour < 12:
                    reasons.append("Morning productivity time")
                elif 13 <= hour < 17:
                    reasons.append("Afternoon focus time")
                elif 17 <= hour < 20:
                    reasons.append("Evening admin time")
            
            # Fit reasons
            if task.duration and pool.available_minutes:
                if task.duration <= pool.available_minutes:
                    utilization = (task.duration / pool.available_minutes) * 100
                    reasons.append(f"Task fits completely ({utilization:.0f}% utilization)")
                else:
                    reasons.append("Task would need to be split")
            
            # Score-based reasons
            if score >= 80:
                reasons.append("Excellent match")
            elif score >= 70:
                reasons.append("Good match")
            elif score >= 60:
                reasons.append("Decent match")
            elif score < 50:
                reasons.append("Poor match")
            
            return reasons
            
        except Exception as e:
            logger.error(f"Error generating match reasons: {e}")
            return ["Match analysis unavailable"]
    
    def auto_assign_task(self, task_id: str, max_pools: int = 3) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Automatically assign a task to the best available time pools
        Returns: (success, message, list_of_assignments)
        """
        try:
            task = Task.query.get(task_id)
            if not task:
                return False, f"Task {task_id} not found", []
            
            if not task.duration:
                return False, "Cannot auto-assign task without duration", []
            
            # Get pool suggestions
            suggestions = self.suggest_pools_for_task(task_id, limit=max_pools * 2)
            if not suggestions:
                return False, "No suitable time pools found", []
            
            assignments_made = []
            remaining_minutes = task.duration
            
            for suggestion in suggestions:
                if remaining_minutes <= 0:
                    break
                
                pool = suggestion['pool']
                pool_id = pool['id']
                available_minutes = pool['available_minutes']
                
                # Determine allocation for this pool
                allocation = min(remaining_minutes, available_minutes)
                
                # Make the assignment
                success, message, assignment = self.assign_task_to_pool(
                    task_id=task_id,
                    time_pool_id=pool_id,
                    allocated_minutes=allocation,
                    assigned_by='system',
                    notes=f"Auto-assigned based on match score {suggestion['match_score']:.1f}"
                )
                
                if success:
                    assignments_made.append(assignment)
                    remaining_minutes -= allocation
                    
                    if len(assignments_made) >= max_pools:
                        break
            
            if assignments_made:
                total_assigned = sum(a['allocated_minutes'] for a in assignments_made)
                if remaining_minutes > 0:
                    return True, f"Partially assigned {total_assigned}/{task.duration} minutes across {len(assignments_made)} pools", assignments_made
                else:
                    return True, f"Fully assigned {total_assigned} minutes across {len(assignments_made)} pools", assignments_made
            else:
                return False, "Failed to make any assignments", []
                
        except Exception as e:
            logger.error(f"Error auto-assigning task {task_id}: {e}")
            return False, f"Auto-assignment failed: {str(e)}", []
    
    def bulk_assign_tasks_to_pools(
        self,
        clear_existing: bool = True,
        max_days_ahead: int = 7,
        assigned_by: str = 'auto_bulk'
    ) -> Dict[str, Any]:
        """
        Bulk assignment of tasks to time pools using pool-by-pool algorithm
        
        Algorithm:
        1. Clear all existing assignments 
        2. Get ALL tasks (including snoozed, blocked, overdue) and sort by priority/due date
        3. Go pool by pool chronologically, filling each with eligible tasks
        4. Remove assigned tasks from queue until queue is empty
        
        Returns: {
            'success': bool,
            'message': str,
            'assignments_made': List[Dict],
            'tasks_processed': int,
            'pools_used': int,
            'unassigned_tasks': List[Dict]
        }
        """
        try:
            logger.info("Starting bulk task assignment process (pool-by-pool)")
            
            # Step 1: Complete wipe of task_assignments table
            if clear_existing:
                # Get count for logging
                assignment_count = TaskAssignment.query.count()
                
                # COMPLETELY CLEAR the task_assignments table
                db.session.query(TaskAssignment).delete()
                
                # Reset all time pool allocations to zero
                all_pools = TimePool.query.all()
                for pool in all_pools:
                    pool.allocated_minutes = 0
                    pool.available_minutes = pool.total_minutes
                    pool.updated_at = datetime.utcnow()
                
                db.session.commit()
                logger.info(f"WIPED {assignment_count} assignments and reset {len(all_pools)} pool allocations")
            
            # Step 2: Get ALL tasks and sort by priority and due date (overdue tasks first)
            task_queue = self._get_all_tasks_for_assignment()
            
            if not task_queue:
                return {
                    'success': True,
                    'message': 'No tasks available for assignment',
                    'assignments_made': [],
                    'tasks_processed': 0,
                    'pools_used': 0,
                    'unassigned_tasks': []
                }
            
            logger.info(f"Got {len(task_queue)} tasks in queue (including snoozed, blocked, overdue)")
            
            # Step 3: Get available time pools in chronological order
            today = date.today()
            end_date = today + timedelta(days=max_days_ahead)
            
            available_pools = TimePool.query.filter(
                TimePool.pool_date >= today,
                TimePool.pool_date <= end_date,
                TimePool.total_minutes > 0
            ).order_by(TimePool.pool_date, TimePool.start_time).all()
            
            if not available_pools:
                return {
                    'success': False,
                    'message': 'No time pools found',
                    'assignments_made': [],
                    'tasks_processed': 0,
                    'pools_used': 0,
                    'unassigned_tasks': [{'id': t['id'], 'title': t.get('title', 'Unknown')} for t in task_queue]
                }
            
            logger.info(f"Found {len(available_pools)} time pools to fill")
            
            # Step 4: Pool-by-pool assignment algorithm
            assignments_made = []
            pools_used = set()
            assigned_task_ids = set()  # Track assigned tasks for blocking logic
            
            # Go through each pool chronologically
            for pool in available_pools:
                logger.debug(f"Filling pool {pool.pool_date} {pool.start_time} ({pool.available_minutes}min available)")
                
                # Try to fill this pool with eligible tasks
                while pool.available_minutes > 0 and task_queue:
                    assigned_task = False
                    
                    # Find first eligible task in queue for this pool
                    for i, task_data in enumerate(task_queue):
                        if self._can_assign_task_to_pool_with_tracking(task_data, pool, assigned_task_ids):
                            # Assign this task to the pool
                            task_duration = min(task_data.get('duration', 30), pool.available_minutes)
                            
                            success, message, assignment_dict = self.assign_task_to_pool(
                                task_id=task_data['id'],
                                time_pool_id=pool.id,
                                allocated_minutes=task_duration,
                                assigned_by=assigned_by,
                                notes="Auto-assigned (pool-by-pool)"
                            )
                            
                            if success and assignment_dict:
                                assignments_made.append({
                                    'task_title': task_data.get('title', 'Unknown'),
                                    'task_id': task_data['id'],
                                    'pool_date': pool.pool_date.isoformat(),
                                    'pool_id': pool.id,
                                    'allocated_minutes': task_duration,
                                    'assignment_id': assignment_dict['id']
                                })
                                pools_used.add(pool.id)
                                assigned_task_ids.add(task_data['id'])  # Track for blocking
                                
                                # Remove task from queue if fully assigned
                                remaining_duration = task_data.get('duration', 30) - task_duration
                                if remaining_duration <= 0:
                                    task_queue.pop(i)
                                else:
                                    # Update task duration for partial assignment
                                    task_data['duration'] = remaining_duration
                                
                                assigned_task = True
                                logger.debug(f"Assigned '{task_data.get('title')}' ({task_duration}min) to pool")
                                break
                            else:
                                logger.warning(f"Failed to assign task {task_data.get('title')}: {message}")
                    
                    # If no task could be assigned to this pool, move to next pool
                    if not assigned_task:
                        break
            
            # Step 5: Return results
            unassigned_tasks = [{'id': t['id'], 'title': t.get('title', 'Unknown')} for t in task_queue]
            
            result = {
                'success': True,
                'message': f"Made {len(assignments_made)} assignments across {len(pools_used)} pools, {len(unassigned_tasks)} tasks remain unassigned",
                'assignments_made': assignments_made,
                'tasks_processed': len(assignments_made) + len(unassigned_tasks),
                'pools_used': len(pools_used),
                'unassigned_tasks': unassigned_tasks
            }
            
            logger.info(f"Bulk assignment complete: {result['message']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk assignment process: {e}")
            return {
                'success': False,
                'message': f"Bulk assignment failed: {str(e)}",
                'assignments_made': [],
                'tasks_processed': 0,
                'pools_used': 0,
                'unassigned_tasks': []
            }
    
    def _get_all_tasks_for_assignment(self) -> List[Dict[str, Any]]:
        """
        Get ALL tasks for assignment including snoozed, blocked, and overdue tasks
        Returns tasks sorted by priority and due date (overdue tasks first)
        """
        try:
            # Get all incomplete tasks
            tasks = Task.query.filter(
                Task.is_completed == False
            ).all()
            
            task_list = []
            for task in tasks:
                task_dict = task.to_dict()
                
                # Calculate priority score (overdue tasks get highest priority)
                # Convert priority to numeric value
                priority_value = task_dict.get('priority', 5)
                if isinstance(priority_value, str):
                    priority_map = {'low': 3, 'medium': 5, 'high': 8, 'urgent': 10}
                    priority_value = priority_map.get(priority_value.lower(), 5)
                
                priority_score = priority_value * 10  # Base priority
                
                if task_dict.get('due_date'):
                    try:
                        if isinstance(task_dict['due_date'], str):
                            due_date = datetime.strptime(task_dict['due_date'], '%Y-%m-%d').date()
                        else:
                            due_date = task_dict['due_date']
                        
                        today = date.today()
                        days_until_due = (due_date - today).days
                        
                        if days_until_due < 0:  # Overdue
                            priority_score += 100 + abs(days_until_due) * 10  # Very high priority
                        elif days_until_due == 0:  # Due today
                            priority_score += 50
                        elif days_until_due <= 3:  # Due soon
                            priority_score += 20
                    except:
                        pass
                
                task_dict['priority_score'] = priority_score
                task_list.append(task_dict)
            
            # Sort by priority score (highest first), then by due date
            # Handle None due dates properly
            def sort_key(task):
                priority_score = task.get('priority_score', 0)
                due_date = task.get('due_date') or '9999-12-31'  # Use far future for None dates
                return (priority_score, due_date)
            
            task_list.sort(key=sort_key, reverse=True)
            
            logger.info(f"Created task queue with {len(task_list)} tasks (including snoozed, blocked, overdue)")
            return task_list
            
        except Exception as e:
            logger.error(f"Error getting all tasks for assignment: {e}")
            return []
    
    def _can_assign_task_to_pool(self, task_data: Dict[str, Any], pool: TimePool) -> bool:
        """
        Check if a task can be assigned to a specific time pool
        
        Eligibility criteria:
        1. Duration: Task fits in remaining pool capacity
        2. Start Date: Pool ENDS after task.snoozed_until datetime
        3. Weather: Pool weather matches task requirements
        4. Blocking: If task is blocked, blocking task must already be assigned
        """
        try:
            # 1. Duration check
            task_duration = task_data.get('duration', 30)
            if task_duration > pool.available_minutes:
                return False
            
            # 2. Start date check (snoozed_until) - pool must END after snooze time
            if task_data.get('snoozed_until'):
                try:
                    if isinstance(task_data['snoozed_until'], str):
                        snooze_until = datetime.fromisoformat(task_data['snoozed_until'].replace('Z', ''))
                    else:
                        snooze_until = task_data['snoozed_until']
                    
                    # Calculate pool end time
                    if isinstance(pool.end_time, datetime):
                        pool_end_time = pool.end_time.time()
                    else:
                        pool_end_time = pool.end_time
                    
                    pool_end_datetime = datetime.combine(pool.pool_date, pool_end_time)
                    
                    # Pool must end AFTER the snooze time
                    if pool_end_datetime <= snooze_until:
                        return False
                        
                except Exception as e:
                    logger.warning(f"Error checking snoozed_until for task {task_data.get('title')}: {e}")
                    return False
            
            # 3. Weather check (if task has weather requirements)
            if task_data.get('required_weather'):
                try:
                    weather = pool.get_weather_forecast()
                    if weather:
                        required_weather = task_data['required_weather']
                        if isinstance(required_weather, str):
                            required_weather = json.loads(required_weather)
                        
                        outdoor_suitable = weather.is_suitable_for_outdoor_work()
                        
                        # Check if weather requirements are met
                        if 'outdoor' in str(required_weather).lower() and not outdoor_suitable:
                            return False
                        elif 'indoor' in str(required_weather).lower() and outdoor_suitable:
                            # Allow indoor tasks in any weather
                            pass
                except:
                    # If weather check fails, allow assignment (don't block on weather errors)
                    pass
            
            # 4. Blocking check - if task is blocked, blocking task must be assigned
            if task_data.get('blocking_task_id'):
                blocking_task_id = task_data['blocking_task_id']
                
                # Check if blocking task has any active assignments
                blocking_assignments = TaskAssignment.query.filter_by(
                    task_id=blocking_task_id
                ).filter(TaskAssignment.status.in_(['assigned', 'started'])).first()
                
                if not blocking_assignments:
                    return False  # Blocking task not yet assigned
            
            return True  # All checks passed
            
        except Exception as e:
            logger.error(f"Error checking task eligibility for pool: {e}")
            return False
    
    def _can_assign_task_to_pool_with_tracking(self, task_data: Dict[str, Any], pool: TimePool, assigned_task_ids: set) -> bool:
        """
        Check if a task can be assigned to a specific time pool with in-memory tracking
        
        Uses in-memory tracking for blocking logic during bulk assignment since we're building 
        assignments from scratch and database may not reflect current state.
        """
        try:
            # 1. Duration check
            task_duration = task_data.get('duration', 30)
            if task_duration > pool.available_minutes:
                return False
            
            # 2. Start date check (snoozed_until) - pool must END after snooze time
            if task_data.get('snoozed_until'):
                try:
                    if isinstance(task_data['snoozed_until'], str):
                        snooze_until = datetime.fromisoformat(task_data['snoozed_until'].replace('Z', ''))
                    else:
                        snooze_until = task_data['snoozed_until']
                    
                    # Calculate pool end time
                    if isinstance(pool.end_time, datetime):
                        pool_end_time = pool.end_time.time()
                    else:
                        pool_end_time = pool.end_time
                    
                    pool_end_datetime = datetime.combine(pool.pool_date, pool_end_time)
                    
                    # Pool must end AFTER the snooze time
                    if pool_end_datetime <= snooze_until:
                        return False
                        
                except Exception as e:
                    logger.warning(f"Error checking snoozed_until for task {task_data.get('title')}: {e}")
                    return False
            
            # 3. Weather check (if task has weather requirements)
            if task_data.get('required_weather'):
                try:
                    weather = pool.get_weather_forecast()
                    if weather:
                        required_weather = task_data['required_weather']
                        if isinstance(required_weather, str):
                            required_weather = json.loads(required_weather)
                        
                        outdoor_suitable = weather.is_suitable_for_outdoor_work()
                        
                        # Check if weather requirements are met
                        if 'outdoor' in str(required_weather).lower() and not outdoor_suitable:
                            return False
                        elif 'indoor' in str(required_weather).lower() and outdoor_suitable:
                            # Allow indoor tasks in any weather
                            pass
                except:
                    # If weather check fails, allow assignment (don't block on weather errors)
                    pass
            
            # 4. Blocking check - use in-memory tracking instead of database
            if task_data.get('blocking_task_id'):
                blocking_task_id = task_data['blocking_task_id']
                
                # Check if blocking task has been assigned in this session
                if blocking_task_id not in assigned_task_ids:
                    return False  # Blocking task not yet assigned
            
            return True  # All checks passed
            
        except Exception as e:
            logger.error(f"Error checking task eligibility for pool with tracking: {e}")
            return False
    
    def _calculate_pool_match_score(self, task_data: Dict[str, Any], pool: TimePool) -> float:
        """
        Calculate how well a task matches a time pool
        Higher score = better match
        """
        score = 0.0
        
        # Base score for having capacity
        if pool.available_minutes >= task_data.get('duration', 30):
            score += 10.0
        
        # Prefer pools with appropriate capacity (not too much wasted space)
        task_duration = task_data.get('duration', 30)
        capacity_ratio = task_duration / pool.available_minutes
        if 0.3 <= capacity_ratio <= 0.8:  # Good utilization
            score += 20.0
        elif capacity_ratio > 0.8:  # High utilization
            score += 15.0
        
        # Date-based scoring
        pool_date = pool.pool_date
        today = date.today()
        
        # Start date (snoozed_until) scoring
        task_start_date = None
        if task_data.get('snoozed_until'):
            if isinstance(task_data['snoozed_until'], str):
                # Parse ISO datetime string and extract date
                task_start_date = datetime.fromisoformat(task_data['snoozed_until'].replace('Z', '')).date()
            else:
                task_start_date = task_data['snoozed_until'].date() if hasattr(task_data['snoozed_until'], 'date') else task_data['snoozed_until']
        
        # Due date scoring
        task_due_date = None
        if task_data.get('due_date'):
            if isinstance(task_data['due_date'], str):
                task_due_date = datetime.strptime(task_data['due_date'], '%Y-%m-%d').date()
            else:
                task_due_date = task_data['due_date']
        
        # Start date constraint - prefer pools closer to start date but not too early
        if task_start_date:
            days_from_start = (pool_date - task_start_date).days
            if days_from_start >= 0:  # Pool is on or after start date
                if days_from_start <= 2:
                    score += 25.0  # Good timing - soon after start
                elif days_from_start <= 7:
                    score += 15.0  # Reasonable timing - within a week
                else:
                    score += 5.0   # Later but still valid
            # Note: pools before start date are already filtered out
        
        # Due date constraint - strongly prefer scheduling before due date
        if task_due_date:
            days_until_due = (task_due_date - pool_date).days
            if days_until_due >= 0:  # Pool is before or on due date
                score += 30.0 + min(days_until_due * 2, 20)  # Bonus for scheduling earlier
            else:  # Pool is after due date
                score -= 50.0  # Heavy penalty
        elif not task_start_date:
            # No due date and no start date - prefer sooner rather than later
            days_from_today = (pool_date - today).days
            score += max(0, 10 - days_from_today)
        
        # Context-based scoring (if implemented)
        if hasattr(pool, 'context_tags') and pool.context_tags:
            # Could add context matching logic here later
            pass
        
        return max(0.0, score)  # Ensure non-negative score

# Global service instance
_assignment_service: Optional[FlaskAssignmentService] = None

def get_assignment_service() -> FlaskAssignmentService:
    """Get the global assignment service instance"""
    global _assignment_service
    if not _assignment_service:
        _assignment_service = FlaskAssignmentService()
    return _assignment_service