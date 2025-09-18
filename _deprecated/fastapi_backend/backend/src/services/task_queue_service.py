"""
Task Queue Service - Priority scoring and scheduling logic
NO EMOJIS
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..data.models.task_model import TaskModel, TaskStatus
from ..data.models.schedule_model import ScheduleModel, TimePoolModel, TaskScheduleModel
from ..data.repositories.task_repo import TaskRepository
from ..data.repositories.schedule_repo import ScheduleRepository, TimePoolRepository, TaskScheduleRepository

logger = logging.getLogger(__name__)

class TaskQueueService:
    """Service for managing task queues and priority scoring"""
    
    def __init__(self, db: Session):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.schedule_repo = ScheduleRepository(db)
        self.time_pool_repo = TimePoolRepository(db)
        self.task_schedule_repo = TaskScheduleRepository(db)
    
    def calculate_priority_score(self, task: TaskModel) -> float:
        """Calculate priority score for a task (higher = more urgent)"""
        score = 0.0
        now = datetime.now()
        today = now.date()
        
        # Base urgency score (1-10)
        urgency_score = task.urgency if task.urgency else 5
        score += urgency_score * 10  # Weight urgency heavily
        
        # Due date scoring
        if task.due_date:
            days_until_due = (task.due_date - today).days
            
            if days_until_due < 0:
                # Overdue tasks get massive priority boost
                overdue_days = abs(days_until_due)
                score += 200 + (overdue_days * 20)  # Escalating penalty for being overdue
            elif days_until_due == 0:
                # Due today
                score += 150
                # Additional boost if due time is soon
                if task.due_time:
                    hours_until_due = (datetime.combine(task.due_date, task.due_time) - now).total_seconds() / 3600
                    if hours_until_due <= 2:
                        score += 50  # Due within 2 hours
                    elif hours_until_due <= 6:
                        score += 30  # Due within 6 hours
            elif days_until_due == 1:
                # Due tomorrow
                score += 100
            elif days_until_due <= 3:
                # Due within 3 days
                score += 75
            elif days_until_due <= 7:
                # Due within a week
                score += 50
            else:
                # Further out - slight boost for having a due date
                score += 20
        else:
            # No due date - slight penalty
            score -= 10
        
        # Duration-based scoring (favor shorter tasks when many are due)
        if task.duration:
            if task.duration <= 30:
                score += 15  # Quick wins
            elif task.duration <= 60:
                score += 10  # Medium tasks
            elif task.duration >= 180:
                score -= 5   # Long tasks get slight penalty
        
        # Snooze penalty
        if task.snoozed_until and task.snoozed_until > now:
            score -= 50  # Snoozed tasks get lower priority
        
        # Project/initiative boost
        if task.project_id:
            score += 25  # Tasks in projects get boost
        if task.initiative_id:
            score += 20  # Initiative tasks get boost
        
        # Completion progress boost
        if task.partial_completion_minutes and task.partial_completion_minutes > 0:
            completion_ratio = task.partial_completion_minutes / (task.duration or 60)
            if completion_ratio >= 0.5:
                score += 40  # Significant progress made
            elif completion_ratio >= 0.25:
                score += 20  # Some progress made
        
        return score
    
    def get_task_queue(
        self,
        include_blocked: bool = False,
        include_snoozed: bool = False,
        date_range_start: Optional[date] = None,
        date_range_end: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get prioritized task queue with scoring"""
        
        # Base query for unscheduled, active tasks
        query = self.db.query(TaskModel).filter(
            TaskModel.status == TaskStatus.ACTIVE
        )
        
        # Exclude tasks that are already scheduled
        scheduled_task_ids = self.db.query(TaskScheduleModel.task_id).filter(
            TaskScheduleModel.is_completed == False
        ).subquery()
        
        query = query.filter(~TaskModel.id.in_(scheduled_task_ids))
        
        # Apply filters
        if not include_blocked:
            # Exclude blocked tasks (tasks with unmet dependencies)
            query = query.filter(
                or_(
                    TaskModel.dependency_task_ids.is_(None),
                    TaskModel.dependency_task_ids == "[]"
                )
            )
        
        if not include_snoozed:
            now = datetime.now()
            query = query.filter(
                or_(
                    TaskModel.snoozed_until.is_(None),
                    TaskModel.snoozed_until <= now
                )
            )
        
        # Date range filter
        if date_range_start or date_range_end:
            if date_range_start and date_range_end:
                query = query.filter(
                    and_(
                        TaskModel.due_date >= date_range_start,
                        TaskModel.due_date <= date_range_end
                    )
                )
            elif date_range_start:
                query = query.filter(TaskModel.due_date >= date_range_start)
            elif date_range_end:
                query = query.filter(TaskModel.due_date <= date_range_end)
        
        # Get tasks and calculate scores
        tasks = query.limit(limit * 2).all()  # Get more than needed for filtering
        
        task_queue_items = []
        for task in tasks:
            priority_score = self.calculate_priority_score(task)
            
            # Check if task can be scheduled
            can_be_scheduled, blocking_reasons = self._can_task_be_scheduled(task)
            
            # Check if overdue
            is_overdue = False
            days_overdue = 0
            if task.due_date:
                days_overdue = (datetime.now().date() - task.due_date).days
                is_overdue = days_overdue > 0
            
            task_item = {
                "task": task,
                "priority_score": priority_score,
                "is_overdue": is_overdue,
                "days_overdue": max(0, days_overdue),
                "can_be_scheduled": can_be_scheduled,
                "blocking_reasons": blocking_reasons
            }
            
            task_queue_items.append(task_item)
        
        # Sort by priority score (descending)
        task_queue_items.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return task_queue_items[:limit]
    
    def get_next_task(self, exclude_task_ids: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get the next highest priority task"""
        exclude_task_ids = exclude_task_ids or []
        
        queue = self.get_task_queue(limit=50)
        
        for item in queue:
            if item["task"].id not in exclude_task_ids and item["can_be_scheduled"]:
                return item
        
        return None
    
    def snooze_task(self, task_id: str, minutes: int, reason: Optional[str] = None) -> bool:
        """Snooze a task for specified minutes"""
        try:
            snooze_until = datetime.now() + timedelta(minutes=minutes)
            
            update_data = {
                "snoozed_until": snooze_until
            }
            
            updated_task = self.task_repo.update(task_id, update_data)
            
            if updated_task:
                logger.info(f"Task {task_id} snoozed for {minutes} minutes until {snooze_until}")
                return True
            else:
                logger.error(f"Failed to snooze task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error snoozing task {task_id}: {e}")
            return False
    
    def add_partial_completion(self, task_id: str, minutes_worked: int, notes: Optional[str] = None) -> bool:
        """Add partial completion minutes to a task"""
        try:
            task = self.task_repo.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            current_partial = task.partial_completion_minutes or 0
            new_partial = current_partial + minutes_worked
            
            update_data = {
                "partial_completion_minutes": new_partial,
                "updated_at": datetime.now()
            }
            
            # If partial completion meets or exceeds duration, mark as completed
            if task.duration and new_partial >= task.duration:
                update_data["status"] = TaskStatus.COMPLETED
                update_data["completed_at"] = datetime.now()
            
            updated_task = self.task_repo.update(task_id, update_data)
            
            if updated_task:
                logger.info(f"Added {minutes_worked} minutes to task {task_id} (total: {new_partial})")
                
                # Generate next recurring task if applicable
                if updated_task.status == TaskStatus.COMPLETED and updated_task.is_recurring:
                    self._generate_next_recurring_task(updated_task)
                
                return True
            else:
                logger.error(f"Failed to update partial completion for task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding partial completion to task {task_id}: {e}")
            return False
    
    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed"""
        try:
            task = self.task_repo.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            update_data = {
                "status": TaskStatus.COMPLETED,
                "completed_at": datetime.now(),
                "last_completed_at": datetime.now()
            }
            
            # Set partial completion to full duration if not already set
            if task.duration and not task.partial_completion_minutes:
                update_data["partial_completion_minutes"] = task.duration
            
            updated_task = self.task_repo.update(task_id, update_data)
            
            if updated_task:
                logger.info(f"Task {task_id} marked as completed")
                
                # Generate next recurring task if applicable
                if updated_task.is_recurring:
                    self._generate_next_recurring_task(updated_task)
                
                return True
            else:
                logger.error(f"Failed to complete task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}")
            return False
    
    def _can_task_be_scheduled(self, task: TaskModel) -> Tuple[bool, List[str]]:
        """Check if a task can be scheduled and return blocking reasons"""
        blocking_reasons = []
        
        # Check if snoozed
        if task.snoozed_until and task.snoozed_until > datetime.now():
            blocking_reasons.append(f"Snoozed until {task.snoozed_until.strftime('%H:%M')}")
        
        # Check dependencies
        if task.dependency_task_ids:
            try:
                import json
                dependency_ids = json.loads(task.dependency_task_ids)
                
                if dependency_ids:
                    incomplete_deps = self.db.query(TaskModel).filter(
                        and_(
                            TaskModel.id.in_(dependency_ids),
                            TaskModel.status != TaskStatus.COMPLETED
                        )
                    ).all()
                    
                    if incomplete_deps:
                        dep_titles = [dep.title for dep in incomplete_deps]
                        blocking_reasons.append(f"Waiting for: {', '.join(dep_titles[:2])}")
                        if len(dep_titles) > 2:
                            blocking_reasons.append(f"and {len(dep_titles) - 2} more")
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Check context conditions (if implemented)
        if task.condition_ids:
            try:
                import json
                condition_ids = json.loads(task.condition_ids)
                if condition_ids:
                    blocking_reasons.append("Context conditions not met")
            except (json.JSONDecodeError, TypeError):
                pass
        
        can_schedule = len(blocking_reasons) == 0
        return can_schedule, blocking_reasons
    
    def _generate_next_recurring_task(self, completed_task: TaskModel):
        """Generate the next occurrence of a recurring task"""
        if not completed_task.is_recurring or not completed_task.recurrence_pattern:
            return
        
        try:
            import json
            from ..utils.recurrence import calculate_next_occurrence
            
            pattern = json.loads(completed_task.recurrence_pattern)
            
            # Calculate next due date
            next_due_date = calculate_next_occurrence(
                completed_task.due_date or datetime.now().date(),
                pattern
            )
            
            if not next_due_date:
                logger.warning(f"Could not calculate next occurrence for task {completed_task.id}")
                return
            
            # Create new task
            new_task_data = {
                "title": completed_task.title,
                "description": completed_task.description,
                "duration": completed_task.duration,
                "urgency": completed_task.urgency,
                "status": TaskStatus.ACTIVE,
                "due_date": next_due_date,
                "due_time": completed_task.due_time,
                "is_recurring": True,
                "recurrence_pattern": completed_task.recurrence_pattern,
                "parent_task_id": completed_task.parent_task_id or completed_task.id,
                "project_id": completed_task.project_id,
                "initiative_id": completed_task.initiative_id,
                "condition_ids": completed_task.condition_ids,
                "dependency_task_ids": completed_task.dependency_task_ids
            }
            
            new_task = self.task_repo.create(new_task_data)
            
            if new_task:
                logger.info(f"Generated next recurring task {new_task.id} for {next_due_date}")
            else:
                logger.error(f"Failed to create next recurring task for {completed_task.id}")
                
        except Exception as e:
            logger.error(f"Error generating next recurring task for {completed_task.id}: {e}")
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get statistics about the task queue"""
        try:
            # Get all unscheduled tasks
            unscheduled_tasks = self.get_task_queue(include_blocked=True, include_snoozed=True, limit=1000)
            
            total_unscheduled = len(unscheduled_tasks)
            schedulable = len([t for t in unscheduled_tasks if t["can_be_scheduled"]])
            blocked = len([t for t in unscheduled_tasks if not t["can_be_scheduled"]])
            overdue = len([t for t in unscheduled_tasks if t["is_overdue"]])
            snoozed = len([t for t in unscheduled_tasks if t["task"].snoozed_until and t["task"].snoozed_until > datetime.now()])
            
            # Calculate priority distribution
            scores = [t["priority_score"] for t in unscheduled_tasks]
            avg_priority = sum(scores) / len(scores) if scores else 0
            high_priority = len([s for s in scores if s >= 150])  # Overdue or due today
            
            return {
                "total_unscheduled": total_unscheduled,
                "schedulable": schedulable,
                "blocked": blocked,
                "overdue": overdue,
                "snoozed": snoozed,
                "average_priority_score": round(avg_priority, 2),
                "high_priority_count": high_priority
            }
            
        except Exception as e:
            logger.error(f"Error getting queue statistics: {e}")
            return {
                "total_unscheduled": 0,
                "schedulable": 0,
                "blocked": 0,
                "overdue": 0,
                "snoozed": 0,
                "average_priority_score": 0,
                "high_priority_count": 0
            }