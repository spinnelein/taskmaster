"""
Initiative repository
NO EMOJIS
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import uuid

from .base import BaseRepository
from ..models.initiative_model import InitiativeModel, InitiativeFrequency, InitiativeStatus
from ..models.task_model import TaskModel

class InitiativeRepository(BaseRepository[InitiativeModel]):
    """Repository for initiative data operations"""
    
    def __init__(self, db: Session):
        super().__init__(InitiativeModel, db)
    
    def create(self, data: Dict[str, Any]) -> InitiativeModel:
        """Create new initiative with enum conversion"""
        # Generate ID if not provided
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        # Convert string frequency to enum
        if 'frequency' in data and isinstance(data['frequency'], str):
            frequency_str = data['frequency'].upper()
            try:
                data['frequency'] = InitiativeFrequency(frequency_str)
            except ValueError:
                data['frequency'] = InitiativeFrequency.WEEKLY  # Default fallback
        
        # Convert string status to enum if provided
        if 'status' in data and isinstance(data['status'], str):
            status_str = data['status'].upper()
            try:
                data['status'] = InitiativeStatus(status_str)
            except ValueError:
                data['status'] = InitiativeStatus.ACTIVE  # Default fallback
        
        entity = self.model(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_active(self) -> List[InitiativeModel]:
        """Get all active initiatives"""
        return self.db.query(self.model).filter(
            self.model.status == InitiativeStatus.ACTIVE
        ).all()
    
    def get_by_frequency(self, frequency: InitiativeFrequency) -> List[InitiativeModel]:
        """Get initiatives by frequency"""
        return self.db.query(self.model).filter(
            self.model.frequency == frequency
        ).all()
    
    def get_templates(self) -> List[InitiativeModel]:
        """Get all initiative templates"""
        return self.db.query(self.model).filter(
            self.model.is_template == True
        ).all()
    
    def get_with_stats(self, initiative_id: str) -> Optional[dict]:
        """Get initiative with completion statistics"""
        initiative = self.get(initiative_id)
        if not initiative:
            return None
        
        # Get all tasks for this initiative
        tasks = self.db.query(TaskModel).filter(
            TaskModel.initiative_id == initiative_id
        ).all()
        
        completed_tasks = [t for t in tasks if t.status.value == "completed"]
        
        # Calculate stats
        total_tasks = len(tasks)
        completed_count = len(completed_tasks)
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # Find last completed task
        last_completed = None
        if completed_tasks:
            last_completed = max(
                completed_tasks, 
                key=lambda t: t.last_completed_at or t.updated_at
            )
        
        return {
            "initiative": initiative,
            "stats": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_count,
                "completion_rate": round(completion_rate, 2),
                "last_completed_at": last_completed.last_completed_at if last_completed else None,
                "average_duration_minutes": self._calculate_average_duration(completed_tasks)
            }
        }
    
    def _calculate_average_duration(self, tasks: List[TaskModel]) -> Optional[int]:
        """Calculate average duration of completed tasks"""
        durations = [t.duration for t in tasks if t.duration]
        if not durations:
            return None
        return sum(durations) // len(durations)
    
    def create_from_template(self, template_id: str, title: str) -> Optional[InitiativeModel]:
        """Create a new initiative from a template"""
        template = self.db.query(self.model).filter(
            and_(
                self.model.id == template_id,
                self.model.is_template == True
            )
        ).first()
        
        if not template:
            return None
        
        # Create new initiative based on template
        new_initiative = InitiativeModel(
            title=title,
            description=template.description,
            frequency=template.frequency,
            interval=template.interval,
            preferred_start_time=template.preferred_start_time,
            estimated_duration_minutes=template.estimated_duration_minutes,
            status=InitiativeStatus.ACTIVE,
            is_template=False
        )
        
        self.db.add(new_initiative)
        self.db.commit()
        self.db.refresh(new_initiative)
        
        # TODO: Copy tasks from template if needed
        
        return new_initiative