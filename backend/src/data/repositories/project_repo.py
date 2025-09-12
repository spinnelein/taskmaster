"""
Project repository
NO EMOJIS
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime
import json

from .base import BaseRepository
from ..models.project_model import ProjectModel, ProjectPhaseModel, ProjectStatus
from ..models.project_template_model import ProjectTemplateModel, TemplateExecutionModel
from ..models.task_model import TaskModel
from ..models.event_model import EventModel

class ProjectRepository(BaseRepository[ProjectModel]):
    """Repository for project data operations"""
    
    def __init__(self, db: Session):
        super().__init__(ProjectModel, db)
    
    def get_with_phases(self, project_id: str) -> Optional[ProjectModel]:
        """Get project with all phases loaded"""
        return self.db.query(self.model).options(
            joinedload(self.model.phases)
        ).filter(
            self.model.id == project_id
        ).first()
    
    def get_active(self) -> List[ProjectModel]:
        """Get all active projects"""
        return self.db.query(self.model).filter(
            self.model.status == ProjectStatus.ACTIVE
        ).all()
    
    def get_by_status(self, status: ProjectStatus) -> List[ProjectModel]:
        """Get projects by status"""
        return self.db.query(self.model).filter(
            self.model.status == status
        ).all()
    
    def get_by_initiative(self, initiative_id: str) -> List[ProjectModel]:
        """Get all projects for an initiative"""
        return self.db.query(self.model).filter(
            self.model.initiative_id == initiative_id
        ).all()
    
    def create_phase(self, project_id: str, phase_data: Dict[str, Any]) -> Optional[ProjectPhaseModel]:
        """Create a new phase for a project"""
        project = self.get(project_id)
        if not project:
            return None
        
        phase = ProjectPhaseModel(
            project_id=project_id,
            **phase_data
        )
        
        self.db.add(phase)
        self.db.commit()
        self.db.refresh(phase)
        
        return phase
    
    def update_phase_status(self, phase_id: str, status: ProjectStatus) -> Optional[ProjectPhaseModel]:
        """Update phase status"""
        phase = self.db.query(ProjectPhaseModel).filter(
            ProjectPhaseModel.id == phase_id
        ).first()
        
        if not phase:
            return None
        
        phase.status = status
        
        # Update actual dates if transitioning
        if status == ProjectStatus.ACTIVE and not phase.actual_start_date:
            phase.actual_start_date = datetime.utcnow()
        elif status == ProjectStatus.COMPLETED and not phase.actual_end_date:
            phase.actual_end_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(phase)
        
        return phase
    
    def execute_template(
        self, 
        template_id: str, 
        project_title: str,
        start_date: Optional[datetime] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[ProjectModel]:
        """Execute a project template to create a new project"""
        template = self.db.query(ProjectTemplateModel).filter(
            ProjectTemplateModel.id == template_id
        ).first()
        
        if not template:
            return None
        
        # Create execution log
        execution = TemplateExecutionModel(
            template_id=template_id,
            execution_parameters=parameters or {},
            success=False
        )
        
        try:
            # Create project
            project = ProjectModel(
                title=project_title,
                description=template.description,
                template_id=template_id,
                status=ProjectStatus.PLANNING,
                estimated_start_date=start_date
            )
            
            self.db.add(project)
            self.db.flush()  # Get project ID
            
            # Create phases from template
            if template.phases_template:
                phases = json.loads(template.phases_template) if isinstance(template.phases_template, str) else template.phases_template
                for phase_data in phases:
                    phase = ProjectPhaseModel(
                        project_id=project.id,
                        title=phase_data.get("title", "Untitled Phase"),
                        description=phase_data.get("description"),
                        order=phase_data.get("order", 0),
                        status=ProjectStatus.PLANNING
                    )
                    self.db.add(phase)
            
            # Create tasks from template
            if template.tasks_template:
                tasks = json.loads(template.tasks_template) if isinstance(template.tasks_template, str) else template.tasks_template
                for task_data in tasks:
                    # TODO: Create tasks based on template
                    pass
            
            # Create events from template
            if template.events_template:
                events = json.loads(template.events_template) if isinstance(template.events_template, str) else template.events_template
                for event_data in events:
                    # TODO: Create events based on template
                    pass
            
            # Update template usage count
            template.usage_count += 1
            
            # Mark execution as successful
            execution.project_id = project.id
            execution.success = True
            execution.execution_log = f"Successfully created project '{project_title}' from template"
            
            self.db.add(execution)
            self.db.commit()
            self.db.refresh(project)
            
            return project
            
        except Exception as e:
            execution.success = False
            execution.error_message = str(e)
            self.db.add(execution)
            self.db.commit()
            self.db.rollback()
            return None
    
    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Get project statistics"""
        project = self.get_with_phases(project_id)
        if not project:
            return {}
        
        # Count tasks
        total_tasks = self.db.query(TaskModel).filter(
            TaskModel.project_id == project_id
        ).count()
        
        completed_tasks = self.db.query(TaskModel).filter(
            and_(
                TaskModel.project_id == project_id,
                TaskModel.status.has(value="completed")
            )
        ).count()
        
        # Count phases
        total_phases = len(project.phases)
        completed_phases = len([p for p in project.phases if p.status == ProjectStatus.COMPLETED])
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "task_completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "phase_completion_rate": (completed_phases / total_phases * 100) if total_phases > 0 else 0
        }