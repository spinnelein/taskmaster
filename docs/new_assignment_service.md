# assignment_service.py - Advanced task-to-pool assignment service with intelligent chunking
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from models import db, Task, TimePool, TaskAssignment
from task_queue_service import get_task_queue_service
import uuid
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

class FlaskAssignmentService:
    """Advanced service for managing task assignments with intelligent prioritization and chunking"""
    
    # Chunking configuration
    CHUNK_SIZES = {
        'minimum': 15,      # Never create chunks smaller than this
        'small': 30,        # Quick work session
        'optimal': 45,      # Ideal focus session
        'extended': 60,     # Extended focus session
        'maximum': 90,      # Maximum single session
        'daily_max': 180    # Maximum daily allocation per large task
    }
    
    def __init__(self):
        self.queue_service = get_task_queue_service()
        self.performance_history = defaultdict(dict)
    
    def calculate_advanced_priority_score(self, task_data: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        """
        Advanced multi-dimensional priority scoring
        Score range: 0-1000 (higher = more urgent)
        """
        context = context or {}
        score = 0.0
        
        # 1. TIME CRITICALITY (0-300 points)
        time_score = self._calculate_time_criticality(task_data)
        
        # 2. URGENCY & IMPORTANCE (0-200 points)
        urgency_score = self._calculate_urgency_importance(task_data)
        
        # 3. PROGRESS MOMENTUM (0-150 points)
        momentum_score = self._calculate_progress_momentum(task_data)
        
        # 4. DEPENDENCY IMPACT (0-150 points)
        dependency_score = self._calculate_dependency_impact(task_data)
        
        # 5. CHUNKING BONUS (0-100 points)
        chunking_score = self._calculate_chunking_priority(task_data)
        
        # 6. EFFORT-REWARD RATIO (0-100 points)
        efficiency_score = self._calculate_effort_reward(task_data)
        
        total_score = sum([
            time_score, urgency_score, momentum_score,
            dependency_score, chunking_score, efficiency_score
        ])
        
        logger.debug(f"Task '{task_data.get('title')}' scores: time={time_score:.1f}, urgency={urgency_score:.1f}, "
                    f"momentum={momentum_score:.1f}, dep={dependency_score:.1f}, chunk={chunking_score:.1f}, "
                    f"efficiency={efficiency_score:.1f}, TOTAL={total_score:.1f}")
        
        return total_score
    
    def _calculate_time_criticality(self, task_data: Dict[str, Any]) -> float:
        """Calculate score based on due date proximity (0-300 points)"""
        score = 0.0
        
        if not task_data.get('due_date'):
            return 0.0  # No due date, no time criticality
        
        try:
            if isinstance(task_data['due_date'], str):
                due_date = datetime.strptime(task_data['due_date'], '%Y-%m-%d').date()
            else:
                due_date = task_data['due_date']
            
            today = date.today()
            days_until_due = (due_date - today).days
            
            if days_until_due < 0:
                # Overdue - escalating penalty
                overdue_days = abs(days_until_due)
                score = 250 + min(50, overdue_days * 5)  # 250-300 points
            elif days_until_due == 0:
                # Due today
                score = 200
            elif days_until_due == 1:
                # Due tomorrow
                score = 150
            elif days_until_due <= 3:
                # Due within 3 days
                score = 100
            elif days_until_due <= 7:
                # Due within a week
                score = 50
            elif days_until_due <= 14:
                # Due within 2 weeks
                score = 25
            else:
                # Due later
                score = 10
            
            # Adjust for task duration (large tasks need to start earlier)
            duration = task_data.get('duration', 30)
            if duration > 240:  # 4+ hour task
                score += min(50, duration / 10)
            elif duration > 120:  # 2+ hour task
                score += min(25, duration / 20)
                
        except Exception as e:
            logger.error(f"Error calculating time criticality: {e}")
        
        return min(300, score)  # Cap at 300
    
    def _calculate_urgency_importance(self, task_data: Dict[str, Any]) -> float:
        """Calculate score based on urgency and priority (0-200 points)"""
        urgency = task_data.get('urgency', 5)
        priority = task_data.get('priority', 'medium')
        
        # Base urgency score (0-100)
        urgency_score = (urgency / 10) * 100
        
        # Priority multiplier
        priority_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5,
            'critical': 2.0,
            'urgent': 2.0
        }
        
        if isinstance(priority, str):
            multiplier = priority_multipliers.get(priority.lower(), 1.0)
        else:
            multiplier = 1.0
        
        return min(200, urgency_score * multiplier)
    
    def _calculate_progress_momentum(self, task_data: Dict[str, Any]) -> float:
        """Calculate score based on existing progress (0-150 points)"""
        score = 0.0
        
        duration = task_data.get('duration', 30)
        partial_completion = task_data.get('partial_completion_minutes', 0)
        
        if partial_completion > 0 and duration > 0:
            completion_ratio = partial_completion / duration
            
            if completion_ratio >= 0.75:
                # Almost done - high priority to finish
                score = 150
            elif completion_ratio >= 0.5:
                # Halfway done - good momentum
                score = 100
            elif completion_ratio >= 0.25:
                # Started - maintain momentum
                score = 50
            else:
                # Just started
                score = 25
        else:
            # Unstarted large tasks get a boost to begin
            if duration > 180:  # 3+ hours
                score = 30
            elif duration > 120:  # 2+ hours
                score = 20
        
        return score
    
    def _calculate_dependency_impact(self, task_data: Dict[str, Any]) -> float:
        """Calculate score based on downstream dependencies (0-150 points)"""
        score = 0.0
        
        # Check if this task blocks others
        blocks_task_ids = task_data.get('blocks_task_ids')
        if blocks_task_ids:
            try:
                if isinstance(blocks_task_ids, str) and blocks_task_ids != 'null':
                    blocked_ids = json.loads(blocks_task_ids)
                    if isinstance(blocked_ids, list) and blocked_ids:
                        # Count and evaluate blocked tasks
                        blocked_count = len(blocked_ids)
                        score = min(150, blocked_count * 30)
                        
                        # Extra points if blocked tasks are urgent
                        blocked_tasks = Task.query.filter(Task.id.in_(blocked_ids)).all()
                        urgent_blocked = sum(1 for t in blocked_tasks if t.urgency and t.urgency >= 7)
                        score += min(50, urgent_blocked * 25)
            except:
                pass
        
        # Check if in a project (project tasks often have implicit dependencies)
        if task_data.get('project_id'):
            score += 20
        
        return min(150, score)
    
    def _calculate_chunking_priority(self, task_data: Dict[str, Any]) -> float:
        """Calculate score bonus for tasks that benefit from chunking (0-100 points)"""
        score = 0.0
        
        duration = task_data.get('duration', 30)
        is_divisible = task_data.get('is_divisible', True)
        partial_completion = task_data.get('partial_completion_minutes', 0)
        
        if not is_divisible:
            return 0.0
        
        # Large unstarted tasks get chunking bonus
        if duration > 240 and partial_completion == 0:  # 4+ hours, unstarted
            score = 100
        elif duration > 180 and partial_completion < 60:  # 3+ hours, barely started
            score = 75
        elif duration > 120:  # 2+ hours
            score = 50
        
        # Overdue large tasks get extra chunking bonus
        if task_data.get('is_overdue') and duration > 90:
            score = min(100, score + 50)
        
        return score
    
    def _calculate_effort_reward(self, task_data: Dict[str, Any]) -> float:
        """Calculate efficiency score based on effort vs impact (0-100 points)"""
        score = 50.0  # Base score
        
        duration = task_data.get('duration', 30)
        
        # Quick wins (high impact, low effort)
        if duration <= 30:
            score += 30
            # Extra bonus for urgent quick tasks
            if task_data.get('urgency', 5) >= 7:
                score += 20
        # Medium effort tasks
        elif duration <= 90:
            score += 10
        # High effort tasks get penalized unless critical
        else:
            if task_data.get('urgency', 5) >= 8 or task_data.get('is_overdue'):
                score += 0  # No penalty for critical large tasks
            else:
                score -= 20  # Penalty for non-critical large tasks
        
        return max(0, min(100, score))
    
    def should_chunk_task(self, task_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Determine if and how to chunk a task
        Returns: (should_chunk, strategy)
        """
        duration = task_data.get('duration', 30)
        is_divisible = task_data.get('is_divisible', True)
        partial_completion = task_data.get('partial_completion_minutes', 0)
        remaining = duration - partial_completion
        
        # Can't chunk if not divisible or too small
        if not is_divisible or remaining <= self.CHUNK_SIZES['extended']:
            return False, None
        
        # MUST chunk if remaining work is too large for single session
        if remaining > self.CHUNK_SIZES['maximum']:
            # Choose strategy based on urgency
            if task_data.get('is_overdue'):
                return True, 'aggressive'
            elif task_data.get('urgency', 5) >= 8:
                return True, 'front_loaded'
            elif task_data.get('due_date'):
                return True, 'deadline_aware'
            else:
                return True, 'distributed'
        
        # SHOULD chunk if it helps with progress distribution
        if remaining > self.CHUNK_SIZES['extended'] and partial_completion == 0:
            # Unstarted large task - get it moving
            return True, 'quick_start'
        
        return False, None
    
    def calculate_chunk_sizes(self, task_data: Dict[str, Any], strategy: str, available_pools: List[TimePool]) -> List[int]:
        """
        Calculate optimal chunk sizes based on strategy
        Returns: List of chunk sizes in minutes
        """
        duration = task_data.get('duration', 30)
        partial_completion = task_data.get('partial_completion_minutes', 0)
        remaining = duration - partial_completion
        
        if strategy == 'aggressive':
            # Front-load with maximum chunks
            chunks = []
            left = remaining
            for _ in range(3):  # First 3 sessions are maximum
                if left <= 0:
                    break
                chunk = min(self.CHUNK_SIZES['maximum'], left)
                chunks.append(chunk)
                left -= chunk
            # Then optimal chunks
            while left > 0:
                chunk = min(self.CHUNK_SIZES['optimal'], left)
                chunks.append(chunk)
                left -= chunk
                
        elif strategy == 'front_loaded':
            # Start with extended sessions, then taper
            chunks = []
            left = remaining
            sizes = [self.CHUNK_SIZES['extended'], self.CHUNK_SIZES['optimal'], self.CHUNK_SIZES['small']]
            size_idx = 0
            while left > 0:
                chunk = min(sizes[min(size_idx, len(sizes)-1)], left)
                chunks.append(chunk)
                left -= chunk
                size_idx += 1
                
        elif strategy == 'quick_start':
            # Small initial chunk to overcome inertia
            chunks = [min(self.CHUNK_SIZES['small'], remaining)]
            left = remaining - chunks[0]
            while left > 0:
                chunk = min(self.CHUNK_SIZES['optimal'], left)
                chunks.append(chunk)
                left -= chunk
                
        elif strategy == 'deadline_aware':
            # Calculate based on days until deadline
            if task_data.get('due_date'):
                try:
                    if isinstance(task_data['due_date'], str):
                        due_date = datetime.strptime(task_data['due_date'], '%Y-%m-%d').date()
                    else:
                        due_date = task_data['due_date']
                    
                    days_until_due = (due_date - date.today()).days
                    if days_until_due > 0:
                        daily_target = remaining / days_until_due
                        # Cap at daily maximum
                        daily_target = min(daily_target, self.CHUNK_SIZES['daily_max'])
                        chunks = []
                        left = remaining
                        while left > 0:
                            chunk = min(daily_target, left, self.CHUNK_SIZES['maximum'])
                            chunks.append(int(chunk))
                            left -= chunk
                    else:
                        # Due today or overdue - aggressive
                        return self.calculate_chunk_sizes(task_data, 'aggressive', available_pools)
                except:
                    # Fall back to distributed
                    return self.calculate_chunk_sizes(task_data, 'distributed', available_pools)
            else:
                # No deadline - use distributed
                return self.calculate_chunk_sizes(task_data, 'distributed', available_pools)
                
        else:  # distributed
            # Even distribution with optimal chunk size
            chunks = []
            left = remaining
            while left > 0:
                chunk = min(self.CHUNK_SIZES['optimal'], left)
                chunks.append(chunk)
                left -= chunk
        
        # Ensure minimum chunk size
        chunks = [c for c in chunks if c >= self.CHUNK_SIZES['minimum']]
        
        # If last chunk is too small, merge with previous
        if len(chunks) > 1 and chunks[-1] < self.CHUNK_SIZES['minimum']:
            chunks[-2] += chunks[-1]
            chunks.pop()
        
        return chunks
    
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
            
            # Check if task has snoozed_until (start date)
            if task.snoozed_until:
                pool_end_datetime = datetime.combine(time_pool.pool_date, time_pool.end_time)
                if pool_end_datetime <= task.snoozed_until:
                    start_time_str = task.snoozed_until.strftime('%Y-%m-%d %H:%M')
                    return False, f"Pool ends before task start time {start_time_str}", None
            
            # Check if task duration allows this allocation
            if task.duration:
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
    
    def smart_assign_task(self, task_id: str, max_pools: int = 5) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Intelligently assign a task using chunking strategies
        Returns: (success, message, list_of_assignments)
        """
        try:
            task = Task.query.get(task_id)
            if not task:
                return False, f"Task {task_id} not found", []
            
            task_data = task.to_dict()
            task_data['is_overdue'] = task.due_date and task.due_date < date.today() if task.due_date else False
            
            # Get available pools
            today = date.today()
            end_date = today + timedelta(days=14)
            available_pools = TimePool.query.filter(
                TimePool.pool_date >= today,
                TimePool.pool_date <= end_date,
                TimePool.available_minutes > 0
            ).order_by(TimePool.pool_date, TimePool.start_time).all()
            
            if not available_pools:
                return False, "No available time pools found", []
            
            # Determine chunking strategy
            should_chunk, strategy = self.should_chunk_task(task_data)
            
            assignments_made = []
            
            if should_chunk:
                # Calculate chunk sizes
                chunk_sizes = self.calculate_chunk_sizes(task_data, strategy, available_pools)
                logger.info(f"Task '{task.title}' will be chunked using '{strategy}' strategy: {chunk_sizes}")
                
                # Assign chunks to pools
                chunk_idx = 0
                for pool in available_pools:
                    if chunk_idx >= len(chunk_sizes):
                        break
                    
                    if pool.available_minutes >= chunk_sizes[chunk_idx]:
                        success, message, assignment = self.assign_task_to_pool(
                            task_id=task_id,
                            time_pool_id=pool.id,
                            allocated_minutes=chunk_sizes[chunk_idx],
                            assigned_by='system',
                            notes=f"Chunk {chunk_idx+1}/{len(chunk_sizes)} ({strategy} strategy)"
                        )
                        
                        if success:
                            assignments_made.append(assignment)
                            chunk_idx += 1
                            
                            if len(assignments_made) >= max_pools:
                                break
                
                if assignments_made:
                    total_assigned = sum(a['allocated_minutes'] for a in assignments_made)
                    return True, f"Task chunked and assigned: {total_assigned} minutes across {len(assignments_made)} sessions", assignments_made
                else:
                    return False, "Failed to assign chunks to available pools", []
                    
            else:
                # Assign whole task to best pool
                best_pool = None
                best_score = 0
                
                for pool in available_pools:
                    if pool.available_minutes >= task.duration:
                        score = self._calculate_pool_match_score(task_data, pool)
                        if score > best_score:
                            best_score = score
                            best_pool = pool
                
                if best_pool:
                    success, message, assignment = self.assign_task_to_pool(
                        task_id=task_id,
                        time_pool_id=best_pool.id,
                        allocated_minutes=task.duration,
                        assigned_by='system',
                        notes=f"Whole task assignment (score: {best_score:.1f})"
                    )
                    
                    if success:
                        return True, f"Task assigned to optimal pool", [assignment]
                    else:
                        return False, message, []
                else:
                    # Try partial assignment
                    for pool in available_pools:
                        if pool.available_minutes >= self.CHUNK_SIZES['minimum']:
                            allocation = min(task.duration, pool.available_minutes)
                            success, message, assignment = self.assign_task_to_pool(
                                task_id=task_id,
                                time_pool_id=pool.id,
                                allocated_minutes=allocation,
                                assigned_by='system',
                                notes="Partial assignment"
                            )
                            
                            if success:
                                return True, f"Partially assigned {allocation} minutes", [assignment]
                    
                    return False, "No suitable pool found for task", []
                    
        except Exception as e:
            logger.error(f"Error in smart assignment for task {task_id}: {e}")
            return False, f"Smart assignment failed: {str(e)}", []
    
    def bulk_assign_with_categories(
        self,
        clear_existing: bool = True,
        max_days_ahead: int = 7,
        assigned_by: str = 'auto_bulk'
    ) -> Dict[str, Any]:
        """
        Advanced bulk assignment with category balancing and chunking
        """
        try:
            logger.info("Starting advanced bulk assignment with category balancing")
            
            # Clear existing if requested
            if clear_existing:
                assignment_count = TaskAssignment.query.count()
                db.session.query(TaskAssignment).delete()
                
                all_pools = TimePool.query.all()
                for pool in all_pools:
                    pool.allocated_minutes = 0
                    pool.available_minutes = pool.total_minutes
                    pool.updated_at = datetime.utcnow()
                
                db.session.commit()
                logger.info(f"Cleared {assignment_count} existing assignments")
            
            # Get all tasks and categorize them
            categories = self._categorize_tasks()
            
            # Get available time pools
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
                    'pools_used': 0
                }
            
            # Calculate time allocation per category
            total_available = sum(p.available_minutes for p in available_pools)
            category_allocations = self._calculate_category_allocations(categories, total_available)
            
            assignments_made = []
            pools_used = set()
            
            # Process each category with its allocation
            for category_name, allocation_minutes in category_allocations.items():
                if category_name not in categories or not categories[category_name]:
                    continue
                
                category_tasks = categories[category_name]
                minutes_used = 0
                
                logger.info(f"Processing {category_name}: {len(category_tasks)} tasks, {allocation_minutes} minutes allocated")
                
                for task_data in category_tasks:
                    if minutes_used >= allocation_minutes:
                        break
                    
                    # Try smart assignment for each task
                    success, message, task_assignments = self.smart_assign_task(task_data['id'])
                    
                    if success:
                        for assignment in task_assignments:
                            assignments_made.append({
                                'task_title': task_data.get('title', 'Unknown'),
                                'task_id': task_data['id'],
                                'category': category_name,
                                'allocated_minutes': assignment['allocated_minutes'],
                                'pool_id': assignment['time_pool_id'],
                                'assignment_id': assignment['id']
                            })
                            minutes_used += assignment['allocated_minutes']
                            pools_used.add(assignment['time_pool_id'])
            
            result = {
                'success': True,
                'message': f"Advanced assignment complete: {len(assignments_made)} assignments across {len(pools_used)} pools",
                'assignments_made': assignments_made,
                'tasks_processed': sum(len(tasks) for tasks in categories.values()),
                'pools_used': len(pools_used),
                'category_summary': {cat: len(tasks) for cat, tasks in categories.items()}
            }
            
            logger.info(f"Bulk assignment complete: {result['message']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk assignment: {e}")
            return {
                'success': False,
                'message': f"Bulk assignment failed: {str(e)}",
                'assignments_made': [],
                'tasks_processed': 0,
                'pools_used': 0
            }
    
    def _categorize_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize all tasks for balanced assignment"""
        categories = {
            'critical_overdue': [],     # Overdue high-priority tasks
            'overdue': [],              # Other overdue tasks
            'due_today': [],            # Due today
            'due_soon': [],             # Due in 1-3 days
            'blocking': [],             # Tasks that block others
            'large_incomplete': [],     # Large tasks with progress
            'large_unstarted': [],      # Large tasks not started
            'quick_wins': [],           # Small tasks < 30 min
            'maintenance': [],          # Recurring tasks
            'standard': []              # Everything else
        }
        
        today = date.today()
        tasks = Task.query.filter(Task.is_completed == False).all()
        
        for task in tasks:
            task_data = task.to_dict()
            
            # Add calculated fields
            task_data['is_overdue'] = False
            task_data['days_until_due'] = None
            
            if task.due_date:
                days_until_due = (task.due_date - today).days
                task_data['days_until_due'] = days_until_due
                task_data['is_overdue'] = days_until_due < 0
            
            # Categorize
            if task_data['is_overdue']:
                if task.urgency and task.urgency >= 7:
                    categories['critical_overdue'].append(task_data)
                else:
                    categories['overdue'].append(task_data)
            elif task_data['days_until_due'] == 0:
                categories['due_today'].append(task_data)
            elif task_data['days_until_due'] and task_data['days_until_due'] <= 3:
                categories['due_soon'].append(task_data)
            elif task.blocks_task_ids:
                categories['blocking'].append(task_data)
            elif task.duration and task.duration > 120:
                if task.partial_completion_minutes and task.partial_completion_minutes > 0:
                    categories['large_incomplete'].append(task_data)
                else:
                    categories['large_unstarted'].append(task_data)
            elif task.duration and task.duration <= 30:
                categories['quick_wins'].append(task_data)
            elif task.recurrence_days and task.recurrence_days > 0:
                categories['maintenance'].append(task_data)
            else:
                categories['standard'].append(task_data)
        
        # Sort tasks within each category by priority score
        for category_name, task_list in categories.items():
            for task in task_list:
                task['priority_score'] = self.calculate_advanced_priority_score(task)
            task_list.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return categories
    
    def _calculate_category_allocations(self, categories: Dict[str, List], total_minutes: int) -> Dict[str, int]:
        """Calculate time allocation for each category"""
        allocations = {}
        
        # Priority-based allocation percentages
        allocation_rules = {
            'critical_overdue': 0.25,   # 25% for critical overdue
            'overdue': 0.15,           # 15% for other overdue
            'due_today': 0.15,          # 15% for due today
            'due_soon': 0.10,           # 10% for due soon
            'blocking': 0.10,           # 10% for blocking tasks
            'large_incomplete': 0.08,   # 8% for incomplete large tasks
            'large_unstarted': 0.05,    # 5% for unstarted large tasks
            'quick_wins': 0.05,         # 5% for quick wins
            'maintenance': 0.03,        # 3% for maintenance
            'standard': 0.04            # 4% for standard tasks
        }
        
        for category, percentage in allocation_rules.items():
            allocations[category] = int(total_minutes * percentage)
        
        # Adjust allocations if some categories are empty
        for category in list(allocations.keys()):
            if category not in categories or not categories[category]:
                # Redistribute this allocation to other categories
                redistribute = allocations[category]
                del allocations[category]
                if allocations:
                    per_category = redistribute // len(allocations)
                    for other_category in allocations:
                        allocations[other_category] += per_category
        
        return allocations
    
    def _calculate_pool_match_score(self, task_data: Dict[str, Any], pool: TimePool) -> float:
        """Enhanced pool matching with time-of-day optimization"""
        score = 50.0  # Base score
        
        try:
            # Due date proximity
            if task_data.get('due_date') and pool.pool_date:
                if isinstance(task_data['due_date'], str):
                    due_date = datetime.strptime(task_data['due_date'], '%Y-%m-%d').date()
                else:
                    due_date = task_data['due_date']
                
                days_until_due = (due_date - pool.pool_date).days
                if days_until_due < 0:
                    score += 30  # Overdue
                elif days_until_due == 0:
                    score += 25  # Due same day
                elif days_until_due <= 2:
                    score += 20  # Due soon
                elif days_until_due <= 7:
                    score += 10  # Due this week
                else:
                    score -= 5   # Due later
            
            # Time-of-day optimization
            if pool.start_time:
                hour = pool.start_time.hour
                task_type = self._infer_task_type(task_data)
                
                time_scores = {
                    'creative': {(7, 12): 20, (12, 14): 5, (14, 20): 10},
                    'analytical': {(9, 14): 20, (14, 17): 15, (17, 20): 5},
                    'routine': {(14, 17): 20, (11, 14): 15, (17, 20): 10},
                    'physical': {(6, 9): 20, (17, 20): 15, (9, 17): 5},
                    'communication': {(10, 12): 15, (14, 17): 20, (9, 10): 10}
                }
                
                if task_type in time_scores:
                    for time_range, points in time_scores[task_type].items():
                        if time_range[0] <= hour < time_range[1]:
                            score += points
                            break
            
            # Weather matching
            weather = pool.get_weather_forecast()
            if weather and task_data.get('required_weather'):
                try:
                    required_weather = json.loads(task_data['required_weather']) if isinstance(task_data['required_weather'], str) else task_data['required_weather']
                    if required_weather:
                        outdoor_suitable = weather.is_suitable_for_outdoor_work()
                        if 'outdoor' in str(required_weather).lower() and outdoor_suitable:
                            score += 15
                        elif 'indoor' in str(required_weather).lower() and not outdoor_suitable:
                            score += 15
                except:
                    pass
            
            # Duration matching
            duration = task_data.get('duration', 30)
            if duration and pool.available_minutes:
                if duration <= pool.available_minutes:
                    utilization = duration / pool.available_minutes
                    if 0.7 <= utilization <= 1.0:
                        score += 15  # Good utilization
                    elif 0.5 <= utilization < 0.7:
                        score += 10  # Decent utilization
                    elif utilization < 0.3:
                        score -= 5   # Poor utilization
                else:
                    score -= 10  # Doesn't fit
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return 50.0
    
    def _infer_task_type(self, task_data: Dict[str, Any]) -> str:
        """Infer task type from title and description"""
        title = task_data.get('title', '').lower()
        description = task_data.get('description', '').lower()
        text = f"{title} {description}"
        
        # Keywords for different task types
        creative_keywords = ['design', 'create', 'write', 'brainstorm', 'plan', 'draft']
        analytical_keywords = ['analyze', 'review', 'research', 'calculate', 'evaluate', 'assess']
        routine_keywords = ['update', 'file', 'organize', 'clean', 'maintain', 'process']
        physical_keywords = ['exercise', 'workout', 'walk', 'run', 'move', 'carry', 'build']
        communication_keywords = ['meet', 'call', 'email', 'discuss', 'present', 'coordinate']
        
        # Check for keyword matches
        if any(keyword in text for keyword in creative_keywords):
            return 'creative'
        elif any(keyword in text for keyword in analytical_keywords):
            return 'analytical'
        elif any(keyword in text for keyword in routine_keywords):
            return 'routine'
        elif any(keyword in text for keyword in physical_keywords):
            return 'physical'
        elif any(keyword in text for keyword in communication_keywords):
            return 'communication'
        else:
            return 'general'
    
    # Keep all the existing methods that aren't being replaced
    def remove_assignment(self, assignment_id: str, reason: str = "Manual removal") -> Tuple[bool, str]:
        """Remove/cancel a task assignment"""
        try:
            assignment = TaskAssignment.query.get(assignment_id)
            if not assignment:
                return False, f"Assignment {assignment_id} not found"
            
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

# Global service instance
_assignment_service: Optional[FlaskAssignmentService] = None

def get_assignment_service() -> FlaskAssignmentService:
    """Get the global assignment service instance"""
    global _assignment_service
    if not _assignment_service:
        _assignment_service = FlaskAssignmentService()
    return _assignment_service