# task_queue_service.py - Flask Task Queue Service with priority scoring
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from models import db, Task, TimePool, TaskAssignment
import json

logger = logging.getLogger(__name__)

class FlaskTaskQueueService:
    """Service for managing task queues and priority scoring in Flask app"""
    
    def __init__(self):
        pass
    
    def calculate_priority_score(self, task: Task) -> float:
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
                    try:
                        due_datetime = datetime.combine(task.due_date, task.due_time)
                        hours_until_due = (due_datetime - now).total_seconds() / 3600
                        if hours_until_due <= 2:
                            score += 50  # Due within 2 hours
                        elif hours_until_due <= 6:
                            score += 30  # Due within 6 hours
                    except:
                        pass  # Ignore time parsing errors
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
        if task.is_snoozed and task.snoozed_until and task.snoozed_until > now:
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
    
    def get_all_tasks_queue(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all tasks ordered by priority score (for display purposes)"""
        
        # Get all incomplete tasks (including snoozed ones)
        current_time = datetime.now()
        tasks = Task.query.filter(Task.is_completed == False).all()
        
        # Auto-unsnooze tasks whose snooze period has ended
        for task in tasks:
            if task.is_snoozed and task.snoozed_until and task.snoozed_until <= current_time:
                task.is_snoozed = False
                task.snoozed_until = None
                task.status = 'active'
        
        db.session.commit()
        
        # Calculate priority scores and create queue items
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
            
            # Check if task is already assigned
            active_assignments = TaskAssignment.query.filter_by(
                task_id=task.id
            ).filter(
                TaskAssignment.status.in_(['assigned', 'started'])
            ).all()
            
            is_assigned = len(active_assignments) > 0
            total_assigned_minutes = sum(a.allocated_minutes for a in active_assignments)
            remaining_minutes = (task.duration or 0) - total_assigned_minutes
            
            # Create task dictionary with additional queue metadata
            task_dict = task.to_dict()
            task_dict.update({
                "priority_score": priority_score,
                "is_overdue": is_overdue,
                "days_overdue": max(0, days_overdue),
                "can_be_scheduled": can_be_scheduled,
                "blocking_reasons": blocking_reasons,
                "is_assigned": is_assigned,
                "is_fully_assigned": is_assigned and remaining_minutes <= 0,
                "assigned_minutes": total_assigned_minutes,
                "remaining_minutes": max(0, remaining_minutes),
                "assignments": [a.to_dict() for a in active_assignments]
            })
            
            task_queue_items.append(task_dict)
        
        # Sort by priority score (descending)
        task_queue_items.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return task_queue_items[:limit]
    
    def get_available_tasks_queue(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get unassigned/partially assigned tasks ordered by priority score (for assignment purposes)"""
        
        all_tasks = self.get_all_tasks_queue(limit * 2)  # Get more to filter from
        
        # Filter to only schedulable tasks that aren't fully assigned
        available_tasks = [
            item for item in all_tasks 
            if item["can_be_scheduled"] and not item["is_fully_assigned"]
        ]
        
        return available_tasks[:limit]
    
    def get_next_task(self, exclude_task_ids: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get the next highest priority available task"""
        exclude_task_ids = exclude_task_ids or []
        
        available_queue = self.get_available_tasks_queue(limit=50)
        
        for item in available_queue:
            if item["task"].id not in exclude_task_ids:
                return item
        
        return None
    
    def _can_task_be_scheduled(self, task: Task) -> Tuple[bool, List[str]]:
        """Check if a task can be scheduled and return blocking reasons"""
        blocking_reasons = []
        
        # Check if snoozed
        if task.is_snoozed and task.snoozed_until and task.snoozed_until > datetime.now():
            blocking_reasons.append(f"Snoozed until {task.snoozed_until.strftime('%m/%d %H:%M')}")
        
        # Check dependencies (using the JSON field from Flask model)
        if task.depends_on_task_ids:
            try:
                # Handle JSON string or null values
                if task.depends_on_task_ids and task.depends_on_task_ids != 'null':
                    dep_ids = json.loads(task.depends_on_task_ids)
                    if isinstance(dep_ids, list) and dep_ids:
                        # Check if any dependencies are incomplete
                        incomplete_deps = Task.query.filter(
                            Task.id.in_(dep_ids),
                            Task.is_completed == False
                        ).all()
                        
                        if incomplete_deps:
                            dep_titles = [dep.title for dep in incomplete_deps]
                            blocking_reasons.append(f"Waiting for: {', '.join(dep_titles[:2])}")
                            if len(dep_titles) > 2:
                                blocking_reasons.append(f"and {len(dep_titles) - 2} more")
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Check required context (if any)
        if task.required_context:
            try:
                # Parse required context JSON
                if task.required_context and task.required_context != 'null':
                    context_reqs = json.loads(task.required_context)
                    if context_reqs:
                        # For now, just note that context is required
                        # Later this can be enhanced with actual context checking
                        blocking_reasons.append("Context requirements not checked")
            except (json.JSONDecodeError, TypeError):
                pass
        
        can_schedule = len(blocking_reasons) == 0
        return can_schedule, blocking_reasons
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get statistics about the task queue"""
        try:
            all_tasks = self.get_all_tasks_queue(limit=1000)
            available_tasks = self.get_available_tasks_queue(limit=1000)
            
            total_tasks = len(all_tasks)
            available_count = len(available_tasks)
            blocked_count = len([t for t in all_tasks if not t["can_be_scheduled"]])
            overdue_count = len([t for t in all_tasks if t["is_overdue"]])
            # Count snoozed tasks - need to check actual Task objects since task dict doesn't have snoozed_until
            snoozed_count = 0
            for t in all_tasks:
                task = Task.query.get(t["id"])
                if task and task.is_snoozed and task.snoozed_until and task.snoozed_until > datetime.now():
                    snoozed_count += 1
            
            # Calculate priority distribution
            scores = [t["priority_score"] for t in all_tasks]
            avg_priority = sum(scores) / len(scores) if scores else 0
            high_priority_count = len([s for s in scores if s >= 150])  # Overdue or due today
            
            # Count assigned tasks
            assigned_count = len([t for t in all_tasks if t["is_assigned"]])
            fully_assigned_count = len([t for t in all_tasks if t["is_fully_assigned"]])
            
            return {
                "total_tasks": total_tasks,
                "available_tasks": available_count,
                "blocked_tasks": blocked_count,
                "overdue_tasks": overdue_count,
                "snoozed_tasks": snoozed_count,
                "assigned_tasks": assigned_count,
                "fully_assigned_tasks": fully_assigned_count,
                "average_priority_score": round(avg_priority, 2),
                "high_priority_count": high_priority_count
            }
            
        except Exception as e:
            logger.error(f"Error getting queue statistics: {e}")
            return {
                "total_tasks": 0,
                "available_tasks": 0,
                "blocked_tasks": 0,
                "overdue_tasks": 0,
                "snoozed_tasks": 0,
                "assigned_tasks": 0,
                "fully_assigned_tasks": 0,
                "average_priority_score": 0,
                "high_priority_count": 0
            }
    
    def snooze_task(self, task_id: str, minutes: int) -> bool:
        """Snooze a task for specified minutes"""
        try:
            task = Task.query.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False
            
            snooze_until = datetime.now() + timedelta(minutes=minutes)
            task.is_snoozed = True
            task.snoozed_until = snooze_until
            task.status = 'snoozed'
            task.updated_at = datetime.now()
            
            db.session.commit()
            logger.info(f"Task {task_id} snoozed for {minutes} minutes until {snooze_until}")
            return True
            
        except Exception as e:
            logger.error(f"Error snoozing task {task_id}: {e}")
            db.session.rollback()
            return False

# Global service instance
_task_queue_service: Optional[FlaskTaskQueueService] = None

def get_task_queue_service() -> FlaskTaskQueueService:
    """Get the global task queue service instance"""
    global _task_queue_service
    if not _task_queue_service:
        _task_queue_service = FlaskTaskQueueService()
    return _task_queue_service