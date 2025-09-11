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
from ...domain.task import Task

class TaskRepository(BaseRepository[Task, TaskModel]):
    """Repository for Task entities"""
    
    def __init__(self, session: Session):
        super().__init__(session, Task, TaskModel)
    
    def _to_domain(self, db_model: TaskModel) -> Task:
        """Convert TaskModel to Task domain entity"""
        task = Task(
            title=db_model.title,
            duration=db_model.duration,
            urgency=db_model.urgency,
            description=db_model.description or "",
            status=db_model.status,
            due_date=db_model.due_date,
            due_time=db_model.due_time
        )
        # Set ID and timestamps from DB
        task.id = db_model.id
        task.created_at = db_model.created_at
        task.updated_at = db_model.updated_at
        task.is_completed = db_model.is_completed
        return task
    
    def _to_db_model(self, domain_model: Task) -> TaskModel:
        """Convert Task domain entity to TaskModel"""
        return TaskModel(
            id=domain_model.id,
            title=domain_model.title,
            duration=domain_model.duration,
            urgency=domain_model.urgency,
            description=domain_model.description,
            status=domain_model.status,
            due_date=domain_model.due_date,
            due_time=domain_model.due_time,
            is_completed=domain_model.is_completed,
            created_at=domain_model.created_at,
            updated_at=domain_model.updated_at
        )
    
    def get_by_status(self, status: str) -> List[Task]:
        """Get tasks by status"""
        db_models = self.session.query(TaskModel).filter(
            TaskModel.status == status
        ).all()
        return [self._to_domain(model) for model in db_models]
    
    def get_pending(self) -> List[Task]:
        """Get all pending tasks"""
        return self.get_by_status("pending")
    
    def get_overdue(self) -> List[Task]:
        """Get overdue tasks"""
        now = datetime.now()
        today = now.date()
        current_time = now.time()
        
        db_models = self.session.query(TaskModel).filter(
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
                overdue_tasks.append(self._to_domain(model))
            elif model.due_date == today and model.due_time and model.due_time < current_time:
                overdue_tasks.append(self._to_domain(model))
        
        return overdue_tasks
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[Task]:
        """Get tasks within date range"""
        db_models = self.session.query(TaskModel).filter(
            and_(
                TaskModel.due_date != None,
                TaskModel.due_date >= start_date,
                TaskModel.due_date <= end_date
            )
        ).all()
        return [self._to_domain(model) for model in db_models]