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
from ..models.initiative_model import InitiativeModel, InitiativeStatus
from ..models.task_model import TaskModel, TaskStatus

class InitiativeRepository(BaseRepository[InitiativeModel]):
    """Repository for initiative data operations"""
    
    def __init__(self, db: Session):
        super().__init__(InitiativeModel, db)
    
    def create(self, data: Dict[str, Any]) -> InitiativeModel:
        """Create new initiative with enum conversion"""
        # Generate ID if not provided
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        # Convert string status to enum if provided
        if 'status' in data and isinstance(data['status'], str):
            status_str = data['status'].lower()
            try:
                data['status'] = InitiativeStatus(status_str)
            except ValueError:
                data['status'] = InitiativeStatus.ACTIVE  # Default fallback
        
        entity = self.model(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[InitiativeModel]:
        """Update initiative with special handling for status changes"""
        initiative = self.get(entity_id)
        if not initiative:
            return None
        
        # Check if status is being changed to completed
        if 'status' in data and isinstance(data['status'], str):
            status_str = data['status'].lower()
            try:
                new_status = InitiativeStatus(status_str)
                # If changing to completed, use the special method
                if new_status == InitiativeStatus.COMPLETED and initiative.status != InitiativeStatus.COMPLETED:
                    # Update other fields first
                    other_data = {k: v for k, v in data.items() if k != 'status'}
                    if other_data:
                        super().update(entity_id, other_data)
                    # Then complete the initiative with tasks
                    return self.complete_initiative_with_tasks(entity_id)
                else:
                    data['status'] = new_status
            except ValueError:
                pass  # Keep the string value, let it fail later if invalid
        
        # For all other updates, use the base update method
        return super().update(entity_id, data)
    
    def get_active(self) -> List[InitiativeModel]:
        """Get all active initiatives"""
        return self.db.query(self.model).filter(
            self.model.status == InitiativeStatus.ACTIVE
        ).all()
    
    def get_with_task_count(self) -> List[Dict[str, Any]]:
        """Get initiatives with task counts"""
        initiatives = self.get_all()
        result = []
        for initiative in initiatives:
            result.append({
                "initiative": initiative,
                "task_count": len(initiative.tasks),
                "active_task_count": len([t for t in initiative.tasks if t.status.value == "active"]),
                "completed_task_count": len([t for t in initiative.tasks if t.status.value == "completed"])
            })
        return result
    
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
            status=InitiativeStatus.ACTIVE,
            is_template=False
        )
        
        self.db.add(new_initiative)
        self.db.commit()
        self.db.refresh(new_initiative)
        
        # TODO: Copy tasks from template if needed
        
        return new_initiative
    
    def complete_initiative_with_tasks(self, initiative_id: str) -> Optional[InitiativeModel]:
        """Mark initiative as completed and complete all its tasks"""
        initiative = self.get(initiative_id)
        if not initiative:
            return None
        
        # Mark the initiative as completed
        initiative.status = InitiativeStatus.COMPLETED
        
        # Mark all associated tasks as completed
        for task in initiative.tasks:
            if task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.COMPLETED
                task.is_completed = True
                task.last_completed_at = datetime.utcnow()
        
        # Update current completion count if target is set
        if initiative.target_completion_count:
            completed_task_count = len([t for t in initiative.tasks if t.status == TaskStatus.COMPLETED])
            initiative.current_completion_count = min(completed_task_count, initiative.target_completion_count)
        
        self.db.commit()
        self.db.refresh(initiative)
        
        return initiative