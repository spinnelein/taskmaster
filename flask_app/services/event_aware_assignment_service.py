# event_aware_assignment_service.py - Event-Aware Assignment Service for TaskMaster YOLO
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import sys
import os
import uuid
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Task, Event, TimePool, Project, ProjectPhase, Meal, TaskAssignment
from assignment_service import FlaskAssignmentService
from services.project_aware_priority_service import get_project_aware_priority_service

logger = logging.getLogger(__name__)

# Constants for meal task generation
DEFAULT_PREP_TIME_MINUTES = 30
PREP_HOURS_BEFORE_MEAL = 24
MAX_PREP_HOURS_BEFORE = 48

class TaskChunkingService:
    """Service for breaking large tasks into manageable chunks"""
    
    def __init__(self):
        self.min_chunk_size = 15  # Minimum chunk size in minutes
        self.max_chunk_size = 120  # Maximum chunk size in minutes
    
    def can_chunk_task(self, task_dict: Dict[str, Any]) -> bool:
        """Check if a task can be broken into chunks"""
        return task_dict.get('is_divisible', False) and task_dict.get('duration', 0) > self.min_chunk_size
    
    def calculate_optimal_chunks(self, task_duration: int, available_slots: List[int]) -> List[int]:
        """Calculate optimal chunk sizes for available time slots"""
        if not available_slots:
            return []
        
        chunks = []
        remaining_duration = task_duration
        
        # Sort slots by size (largest first) for better utilization
        sorted_slots = sorted(available_slots, reverse=True)
        
        for slot_size in sorted_slots:
            if remaining_duration <= 0:
                break
            
            # Calculate chunk size for this slot
            chunk_size = min(remaining_duration, slot_size, self.max_chunk_size)
            
            # Only create chunk if it meets minimum size
            if chunk_size >= self.min_chunk_size:
                chunks.append(chunk_size)
                remaining_duration -= chunk_size
        
        return chunks

class EventAwareAssignmentService(FlaskAssignmentService):
    """Assignment service that respects events and project structure"""
    
    def __init__(self):
        super().__init__()
        self.priority_service = get_project_aware_priority_service()
        self.chunking_service = TaskChunkingService()
    
    def get_available_pools_with_events(self, start_date: date, end_date: date) -> List[TimePool]:
        """Get time pools that don't conflict with events"""
        try:
            pools = TimePool.query.filter(
                TimePool.pool_date >= start_date,
                TimePool.pool_date <= end_date,
                TimePool.available_minutes > 0
            ).all()
            
            # Check each pool for event conflicts
            available_pools = []
            for pool in pools:
                if not self._has_event_conflict(pool):
                    available_pools.append(pool)
            
            logger.info(f"Found {len(available_pools)} conflict-free pools out of {len(pools)} total")
            return available_pools
            
        except Exception as e:
            logger.error(f"Error getting available pools with events: {e}")
            return []
    
    def _has_event_conflict(self, pool: TimePool) -> bool:
        """Check if pool overlaps with any blocking events"""
        try:
            pool_start = datetime.combine(pool.pool_date, pool.start_time.time())
            pool_end = datetime.combine(pool.pool_date, pool.end_time.time())
            
            # Find overlapping blocking events
            events = Event.query.filter(
                Event.is_blocking == True,
                Event.start_time < pool_end,
                Event.end_time > pool_start
            ).all()
            
            if events:
                logger.debug(f"Pool {pool.id} conflicts with {len(events)} blocking events")
                return True
            return False
            
        except Exception as e:
            logger.warning(f"Error checking event conflict for pool {pool.id}: {e}")
            return False
    
    def assign_project_tasks_smart(self, project_id: str) -> Dict[str, Any]:
        """Assign all tasks in a project respecting dependencies"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'success': False, 'message': 'Project not found'}
            
            # Get all incomplete project tasks
            tasks = Task.query.filter_by(
                project_id=project_id,
                is_completed=False
            ).all()
            
            if not tasks:
                return {
                    'success': True,
                    'message': 'No incomplete tasks found in project',
                    'project': project.title,
                    'tasks_assigned': 0,
                    'assignments': []
                }
            
            # Convert to dicts for processing
            task_dicts = [task.to_dict() for task in tasks]
            
            # Build dependency graph
            task_graph = self._build_dependency_graph(task_dicts)
            
            # Get topological order (respecting dependencies)
            ordered_tasks = self._topological_sort(task_graph)
            
            # Get available pools
            today = date.today()
            end_date = today + timedelta(days=14)  # Look ahead 2 weeks
            available_pools = self.get_available_pools_with_events(today, end_date)
            
            if not available_pools:
                return {
                    'success': False,
                    'message': 'No available time pools found',
                    'project': project.title,
                    'tasks_assigned': 0,
                    'assignments': []
                }
            
            # Assign in dependency order
            assignments = []
            for task_dict in ordered_tasks:
                # Only assign if dependencies are satisfied
                if self._dependencies_satisfied(task_dict, task_dicts):
                    result = self._assign_task_smartly(task_dict, available_pools)
                    if result:
                        assignments.extend(result)
            
            return {
                'success': True,
                'project': project.title,
                'tasks_assigned': len(assignments),
                'assignments': assignments,
                'message': f"Assigned {len(assignments)} tasks from project '{project.title}'"
            }
            
        except Exception as e:
            logger.error(f"Error in smart project assignment for {project_id}: {e}")
            return {
                'success': False,
                'message': f"Smart assignment failed: {str(e)}",
                'assignments': []
            }
    
    def _build_dependency_graph(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build task dependency relationships"""
        graph = {}
        task_ids = {task['id'] for task in tasks}
        
        for task in tasks:
            task_id = task['id']
            graph[task_id] = []
            
            # Parse dependencies
            depends_on = task.get('depends_on_task_ids')
            if depends_on:
                try:
                    if isinstance(depends_on, str):
                        deps = json.loads(depends_on) if depends_on != 'null' else []
                    else:
                        deps = depends_on or []
                    
                    # Only include dependencies that are in our task set
                    graph[task_id] = [dep_id for dep_id in deps if dep_id in task_ids]
                except Exception as e:
                    logger.warning(f"Error parsing dependencies for task {task_id}: {e}")
        
        return graph
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Order tasks respecting dependencies using topological sort"""
        try:
            # Calculate in-degrees
            in_degree = {node: 0 for node in graph}
            for node in graph:
                for neighbor in graph[node]:
                    if neighbor in in_degree:
                        in_degree[neighbor] += 1
            
            # Queue of nodes with no dependencies
            queue = [node for node in in_degree if in_degree[node] == 0]
            result = []
            
            while queue:
                node = queue.pop(0)
                result.append(node)
                
                # Remove this node from graph and update in-degrees
                for neighbor in graph[node]:
                    if neighbor in in_degree:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)
            
            # Convert back to task dicts with priority scoring
            task_lookup = {task['id']: task for task in self._get_all_tasks_for_assignment()}
            ordered_task_dicts = []
            
            for task_id in result:
                if task_id in task_lookup:
                    task_dict = task_lookup[task_id]
                    # Add priority score for secondary sorting
                    task_dict['priority_score'] = self.priority_service.calculate_priority_score(task_dict)
                    ordered_task_dicts.append(task_dict)
            
            # Sort by priority within dependency constraints
            return ordered_task_dicts
            
        except Exception as e:
            logger.error(f"Error in topological sort: {e}")
            return []
    
    def _dependencies_satisfied(self, task_dict: Dict[str, Any], all_tasks: List[Dict[str, Any]]) -> bool:
        """Check if task dependencies are met (completed or assigned)"""
        try:
            depends_on = task_dict.get('depends_on_task_ids')
            if not depends_on:
                return True
            
            if isinstance(depends_on, str):
                deps = json.loads(depends_on) if depends_on != 'null' else []
            else:
                deps = depends_on or []
            
            if not deps:
                return True
            
            # Check each dependency
            for dep_id in deps:
                dep_task = next((t for t in all_tasks if t['id'] == dep_id), None)
                if dep_task:
                    # Check if completed
                    if dep_task.get('completed', False):
                        continue
                    
                    # Check if assigned
                    assignments = TaskAssignment.query.filter_by(
                        task_id=dep_id
                    ).filter(TaskAssignment.status.in_(['assigned', 'started'])).first()
                    
                    if not assignments:
                        return False  # Dependency not satisfied
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking dependencies for task {task_dict.get('id')}: {e}")
            return True  # Default to allow assignment if check fails
    
    def _assign_task_smartly(self, task_dict: Dict[str, Any], available_pools: List[TimePool]) -> List[Dict[str, Any]]:
        """Assign a single task to best available pools"""
        try:
            task_id = task_dict['id']
            duration = task_dict.get('duration', 30)
            
            # Get pool suggestions using parent class logic
            suggestions = self.suggest_pools_for_task(task_id, limit=10)
            if not suggestions:
                logger.warning(f"No pool suggestions for task {task_dict.get('title', task_id)}")
                return []
            
            # Filter suggestions to only conflict-free pools
            filtered_suggestions = []
            available_pool_ids = {pool.id for pool in available_pools}
            
            for suggestion in suggestions:
                pool_id = suggestion['pool']['id']
                if pool_id in available_pool_ids:
                    filtered_suggestions.append(suggestion)
            
            if not filtered_suggestions:
                logger.warning(f"No conflict-free pools for task {task_dict.get('title', task_id)}")
                return []
            
            # Try to assign to best pools
            assignments = []
            remaining_duration = duration
            
            for suggestion in filtered_suggestions[:3]:  # Try top 3 pools
                if remaining_duration <= 0:
                    break
                
                pool = suggestion['pool']
                allocation = min(remaining_duration, pool['available_minutes'])
                
                success, message, assignment = self.assign_task_to_pool(
                    task_id=task_id,
                    time_pool_id=pool['id'],
                    allocated_minutes=allocation,
                    assigned_by='smart_system',
                    notes=f"Smart assignment (score: {suggestion['match_score']:.1f})"
                )
                
                if success:
                    assignments.append(assignment)
                    remaining_duration -= allocation
                    
                    # Update pool availability for subsequent assignments
                    for avail_pool in available_pools:
                        if avail_pool.id == pool['id']:
                            avail_pool.allocated_minutes += allocation
                            avail_pool.available_minutes -= allocation
                            break
            
            if assignments:
                logger.info(f"Smart assigned task '{task_dict.get('title')}' to {len(assignments)} pools")
            
            return assignments
            
        except Exception as e:
            logger.error(f"Error in smart task assignment for {task_dict.get('id')}: {e}")
            return []
    
    def handle_recurring_tasks(self) -> Dict[str, Any]:
        """Process recurring tasks that need regeneration"""
        try:
            current_time = datetime.now()
            
            # Find recurring tasks that need processing
            recurring_tasks = Task.query.filter(
                Task.recurrence_days > 0,
                Task.is_snoozed == True,
                Task.snoozed_until <= current_time
            ).all()
            
            processed = []
            for task in recurring_tasks:
                # Unsnooze the task
                task.is_snoozed = False
                task.snoozed_until = None
                task.status = 'active'
                
                # Reset any partial completion
                task.partial_completion_minutes = 0
                
                # Update timestamp
                task.updated_at = current_time
                
                processed.append(task.title)
                logger.info(f"Reactivated recurring task: {task.title}")
            
            db.session.commit()
            
            return {
                'success': True,
                'processed': len(processed),
                'tasks': processed,
                'message': f"Reactivated {len(processed)} recurring tasks"
            }
            
        except Exception as e:
            logger.error(f"Error handling recurring tasks: {e}")
            db.session.rollback()
            return {
                'success': False,
                'processed': 0,
                'tasks': [],
                'message': f"Failed to process recurring tasks: {str(e)}"
            }
    
    def prepare_meal_tasks(self, date_range: int = 3) -> Dict[str, Any]:
        """Create tasks for upcoming meal preparation"""
        try:
            end_date = datetime.now() + timedelta(days=date_range)
            current_time = datetime.now()
            
            # Find upcoming meals that need prep tasks
            meals = Meal.query.filter(
                Meal.planned_date <= end_date,
                Meal.status == 'planned'
            ).all()
            
            tasks_created = []
            for meal in meals:
                # Skip if meal doesn't have serve time
                if not meal.serve_time:
                    continue
                
                # Calculate hours before meal
                hours_before_meal = (meal.serve_time - current_time).total_seconds() / 3600
                
                # Only create prep tasks if within reasonable timeframe
                if PREP_HOURS_BEFORE_MEAL <= hours_before_meal <= MAX_PREP_HOURS_BEFORE:
                    # Check if prep task already exists
                    existing_prep = Task.query.filter_by(
                        meal_id=meal.id,
                        title=f"Prepare {meal.title}"
                    ).first()
                    
                    if not existing_prep:
                        # Calculate total prep time from dishes
                        total_prep_time = self._calculate_meal_prep_time(meal)
                        
                        # Create prep task
                        prep_task = Task(
                            id=str(uuid.uuid4()),
                            title=f"Prepare {meal.title}",
                            description=f"Prep ingredients and setup for {meal.meal_type}: {meal.title}",
                            duration=total_prep_time,
                            urgency=8,  # High urgency for meal prep
                            priority='high',
                            status='active',
                            due_date=meal.planned_date.date() if meal.planned_date else None,
                            meal_id=meal.id,
                            is_completed=False,
                            created_at=current_time,
                            updated_at=current_time
                        )
                        
                        db.session.add(prep_task)
                        tasks_created.append(prep_task.title)
                        logger.info(f"Created meal prep task: {prep_task.title}")
                
                # Create cooking task if very close to serve time
                if 0.5 <= hours_before_meal <= 3:
                    existing_cook = Task.query.filter_by(
                        meal_id=meal.id,
                        title=f"Cook {meal.title}"
                    ).first()
                    
                    if not existing_cook:
                        # Calculate cooking time
                        cook_time = self._calculate_meal_cook_time(meal)
                        
                        cook_task = Task(
                            id=str(uuid.uuid4()),
                            title=f"Cook {meal.title}",
                            description=f"Cook and serve {meal.meal_type}: {meal.title}",
                            duration=cook_time,
                            urgency=9,  # Very high urgency for cooking
                            priority='urgent',
                            status='active',
                            due_date=meal.planned_date.date() if meal.planned_date else None,
                            meal_id=meal.id,
                            is_completed=False,
                            created_at=current_time,
                            updated_at=current_time
                        )
                        
                        db.session.add(cook_task)
                        tasks_created.append(cook_task.title)
                        logger.info(f"Created meal cook task: {cook_task.title}")
            
            db.session.commit()
            
            return {
                'success': True,
                'meals_checked': len(meals),
                'tasks_created': len(tasks_created),
                'tasks': tasks_created,
                'message': f"Created {len(tasks_created)} meal tasks from {len(meals)} upcoming meals"
            }
            
        except Exception as e:
            logger.error(f"Error preparing meal tasks: {e}")
            db.session.rollback()
            return {
                'success': False,
                'meals_checked': 0,
                'tasks_created': 0,
                'tasks': [],
                'message': f"Failed to prepare meal tasks: {str(e)}"
            }
    
    def _calculate_meal_prep_time(self, meal: Meal) -> int:
        """Calculate total prep time for a meal based on its dishes"""
        try:
            dishes = meal.get_dishes()
            total_prep_time = 0
            
            for dish in dishes:
                prep_time = dish.prep_time_minutes or DEFAULT_PREP_TIME_MINUTES
                total_prep_time += prep_time
            
            # Add 15 minutes base prep time for setup/cleanup
            return max(total_prep_time + 15, DEFAULT_PREP_TIME_MINUTES)
            
        except Exception as e:
            logger.warning(f"Error calculating prep time for meal {meal.id}: {e}")
            return DEFAULT_PREP_TIME_MINUTES
    
    def _calculate_meal_cook_time(self, meal: Meal) -> int:
        """Calculate total cook time for a meal based on its dishes"""
        try:
            dishes = meal.get_dishes()
            total_cook_time = 0
            
            for dish in dishes:
                cook_time = dish.cook_time_minutes or 30
                # Use max instead of sum for concurrent cooking
                total_cook_time = max(total_cook_time, cook_time)
            
            # Add 10 minutes for plating/serving
            return max(total_cook_time + 10, 30)
            
        except Exception as e:
            logger.warning(f"Error calculating cook time for meal {meal.id}: {e}")
            return 30
    
    def bulk_assign_with_events(
        self,
        clear_existing: bool = True,
        max_days_ahead: int = 7,
        respect_project_structure: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced bulk assignment that respects events and project dependencies
        """
        try:
            logger.info("Starting event-aware bulk assignment")
            
            # Step 1: Clear existing assignments if requested
            if clear_existing:
                assignment_count = TaskAssignment.query.count()
                db.session.query(TaskAssignment).delete()
                
                # Reset all time pool allocations
                all_pools = TimePool.query.all()
                for pool in all_pools:
                    pool.allocated_minutes = 0
                    pool.available_minutes = pool.total_minutes
                    pool.updated_at = datetime.utcnow()
                
                db.session.commit()
                logger.info(f"Cleared {assignment_count} existing assignments")
            
            # Step 2: Get conflict-free time pools
            today = date.today()
            end_date = today + timedelta(days=max_days_ahead)
            available_pools = self.get_available_pools_with_events(today, end_date)
            
            if not available_pools:
                return {
                    'success': False,
                    'message': 'No conflict-free time pools found',
                    'assignments_made': [],
                    'tasks_processed': 0,
                    'pools_used': 0
                }
            
            # Step 3: Get and prioritize tasks
            all_tasks = self._get_all_tasks_for_assignment()
            
            # Add priority scores using project-aware service
            for task in all_tasks:
                task['priority_score'] = self.priority_service.calculate_priority_score(task, all_tasks)
            
            # Sort by priority score
            all_tasks.sort(key=lambda t: t['priority_score'], reverse=True)
            
            # Step 4: Assign tasks pool by pool
            assignments_made = []
            pools_used = set()
            
            for pool in available_pools:
                logger.debug(f"Processing pool {pool.pool_date} {pool.start_time}")
                
                # Find best task for this pool
                pool_filled = False
                for i, task_data in enumerate(all_tasks):
                    if pool.available_minutes <= 0:
                        break
                    
                    # Check if task can be assigned to this pool
                    if self._can_assign_task_to_pool_with_events(task_data, pool):
                        # Calculate allocation
                        task_duration = min(task_data.get('duration', 30), pool.available_minutes)
                        
                        # Make assignment
                        success, message, assignment_dict = self.assign_task_to_pool(
                            task_id=task_data['id'],
                            time_pool_id=pool.id,
                            allocated_minutes=task_duration,
                            assigned_by='event_aware_bulk',
                            notes="Event-aware bulk assignment"
                        )
                        
                        if success and assignment_dict:
                            assignments_made.append({
                                'task_title': task_data.get('title', 'Unknown'),
                                'task_id': task_data['id'],
                                'pool_date': pool.pool_date.isoformat(),
                                'pool_id': pool.id,
                                'allocated_minutes': task_duration,
                                'assignment_id': assignment_dict['id'],
                                'priority_score': task_data.get('priority_score', 0)
                            })
                            pools_used.add(pool.id)
                            
                            # Remove or update task in queue
                            remaining_duration = task_data.get('duration', 30) - task_duration
                            if remaining_duration <= 0:
                                all_tasks.pop(i)
                            else:
                                task_data['duration'] = remaining_duration
                            
                            pool_filled = True
                            break
                
                if not pool_filled:
                    logger.debug(f"No suitable tasks found for pool {pool.id}")
            
            # Step 5: Return results
            unassigned_tasks = [{'id': t['id'], 'title': t.get('title', 'Unknown')} for t in all_tasks]
            
            result = {
                'success': True,
                'message': f"Event-aware assignment: {len(assignments_made)} assignments across {len(pools_used)} pools",
                'assignments_made': assignments_made,
                'tasks_processed': len(assignments_made) + len(unassigned_tasks),
                'pools_used': len(pools_used),
                'unassigned_tasks': unassigned_tasks,
                'conflict_free_pools': len(available_pools)
            }
            
            logger.info(result['message'])
            return result
            
        except Exception as e:
            logger.error(f"Error in event-aware bulk assignment: {e}")
            return {
                'success': False,
                'message': f"Event-aware assignment failed: {str(e)}",
                'assignments_made': [],
                'tasks_processed': 0,
                'pools_used': 0
            }
    
    def _can_assign_task_to_pool_with_events(self, task_data: Dict[str, Any], pool: TimePool) -> bool:
        """Check if task can be assigned considering events and dependencies"""
        # Use parent class logic for basic checks
        if not self._can_assign_task_to_pool(task_data, pool):
            return False
        
        # Additional event conflict check (redundant but explicit)
        if self._has_event_conflict(pool):
            return False
        
        return True

# Global service instance
_event_aware_assignment_service: Optional[EventAwareAssignmentService] = None

def get_event_aware_assignment_service() -> EventAwareAssignmentService:
    """Get the global event-aware assignment service instance"""
    global _event_aware_assignment_service
    if not _event_aware_assignment_service:
        _event_aware_assignment_service = EventAwareAssignmentService()
    return _event_aware_assignment_service