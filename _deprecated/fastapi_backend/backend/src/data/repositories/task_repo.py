"""
Task repository implementation
NO EMOJIS
"""
from typing import Optional, List
from datetime import date, datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base import BaseRepository
from ..models.task_model import TaskModel

class TaskRepository(BaseRepository[TaskModel]):
    """Repository for Task entities"""
    
    def __init__(self, db: Session):
        super().__init__(TaskModel, db)
    
    def get_by_status(self, status: str) -> List[TaskModel]:
        """Get tasks by status"""
        return self.db.query(TaskModel).filter(
            TaskModel.status == status
        ).all()
    
    def get_pending(self) -> List[TaskModel]:
        """Get all pending tasks"""
        return self.get_by_status("pending")
    
    def get_overdue(self) -> List[TaskModel]:
        """Get overdue tasks"""
        now = datetime.now()
        today = now.date()
        current_time = now.time()
        
        db_models = self.db.query(TaskModel).filter(
            and_(
                TaskModel.status != "completed",
                TaskModel.due_date != None,
                TaskModel.due_date <= today
            )
        ).all()
        
        overdue_tasks = []
        for model in db_models:
            # Check if task is overdue
            if model.due_date < today:
                overdue_tasks.append(model)
            elif model.due_date == today and model.due_time and model.due_time < current_time:
                overdue_tasks.append(model)
        
        return overdue_tasks
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[TaskModel]:
        """Get tasks within date range"""
        return self.db.query(TaskModel).filter(
            and_(
                TaskModel.due_date != None,
                TaskModel.due_date >= start_date,
                TaskModel.due_date <= end_date
            )
        ).all()
    
    def get_recurring(self) -> List[TaskModel]:
        """Get recurring tasks"""
        return self.db.query(TaskModel).filter(
            TaskModel.is_recurring == True
        ).all()
    
    def get_snoozed(self) -> List[TaskModel]:
        """Get snoozed tasks"""
        return self.db.query(TaskModel).filter(
            TaskModel.snoozed_until != None,
            TaskModel.snoozed_until > datetime.now()
        ).all()
    
    def get_blocked(self) -> List[TaskModel]:
        """Get blocked tasks (with unmet dependencies)"""
        return self.db.query(TaskModel).filter(
            TaskModel.condition_ids != None,
            TaskModel.status != "completed"
        ).all()