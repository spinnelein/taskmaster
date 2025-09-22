# projects.py - Project domain models: Initiative, Project, ProjectPhase
from .base import db, BaseModel
from sqlalchemy import text


class Initiative(BaseModel):
    __tablename__ = 'initiatives'
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20))  # ACTIVE, COMPLETED, PAUSED
    is_template = db.Column(db.Boolean, default=False)
    target_completion_count = db.Column(db.Integer)
    current_completion_count = db.Column(db.Integer, default=0)
    
    # Following plan.md - initiatives should have task_templates JSON field
    # For now, we'll work with existing schema and add task_templates functionality in API layer
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'status': self.status or 'ACTIVE',
            'is_template': bool(self.is_template),
            'target_completion_count': self.target_completion_count or 0,
            'current_completion_count': self.current_completion_count or 0,
            'progress_percentage': self.calculate_progress(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'task_count': self.get_task_count()
        }
    
    def calculate_progress(self):
        """Calculate completion percentage"""
        if not self.target_completion_count or self.target_completion_count == 0:
            return 0
        percentage = (self.current_completion_count / self.target_completion_count) * 100
        return min(100, max(0, round(percentage, 1)))
    
    def get_task_count(self):
        """Get count of tasks associated with this initiative"""
        # In Flask, we'll query tasks separately to avoid relationship issues
        result = db.session.execute(
            text("SELECT COUNT(*) FROM tasks WHERE initiative_id = :init_id AND is_completed = 0"),
            {"init_id": self.id}
        ).scalar()
        return result or 0


class Project(BaseModel):
    __tablename__ = 'projects'
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(9), nullable=False)  # PLANNING, ACTIVE, COMPLETED
    priority = db.Column(db.String(8), nullable=False)  # LOW, MEDIUM, HIGH
    estimated_start_date = db.Column(db.DateTime)
    estimated_end_date = db.Column(db.DateTime)
    actual_start_date = db.Column(db.DateTime)
    actual_end_date = db.Column(db.DateTime)
    initiative_id = db.Column(db.String(36))
    template_id = db.Column(db.String(36))
    tags = db.Column(db.Text)  # JSON
    custom_fields = db.Column(db.Text)  # JSON
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'status': self.status,
            'priority': self.priority,
            'estimated_start_date': self.estimated_start_date.isoformat() if self.estimated_start_date else None,
            'estimated_end_date': self.estimated_end_date.isoformat() if self.estimated_end_date else None,
            'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'initiative_id': self.initiative_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ProjectPhase(BaseModel):
    __tablename__ = 'project_phases'
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(9), nullable=False)  # PLANNING, ACTIVE, COMPLETED
    estimated_start_date = db.Column(db.DateTime)
    estimated_end_date = db.Column(db.DateTime)
    actual_start_date = db.Column(db.DateTime)
    actual_end_date = db.Column(db.DateTime)
    depends_on_phase_ids = db.Column(db.Text)  # JSON
    project_id = db.Column(db.String(36), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'order': self.order,
            'status': self.status,
            'estimated_start_date': self.estimated_start_date.isoformat() if self.estimated_start_date else None,
            'estimated_end_date': self.estimated_end_date.isoformat() if self.estimated_end_date else None,
            'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'depends_on_phase_ids': self.depends_on_phase_ids,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ProjectTemplate(BaseModel):
    __tablename__ = 'project_templates'
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # e.g., "Marketing Campaign", "Product Launch", "Research Project"
    template_data = db.Column(db.Text, nullable=False)  # JSON containing project structure
    estimated_duration_days = db.Column(db.Integer)  # Total estimated duration
    is_active = db.Column(db.Boolean, default=True)  # Whether template is available for use
    usage_count = db.Column(db.Integer, default=0)  # How many times this template has been used
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'category': self.category or 'General',
            'template_data': json.loads(self.template_data) if self.template_data else {},
            'estimated_duration_days': self.estimated_duration_days or 0,
            'is_active': bool(self.is_active),
            'usage_count': self.usage_count or 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def set_template_data(self, data_dict):
        """Set template data from a dictionary"""
        import json
        self.template_data = json.dumps(data_dict, indent=2)
    
    def get_template_data(self):
        """Get template data as a dictionary"""
        import json
        return json.loads(self.template_data) if self.template_data else {}
    
    def increment_usage(self):
        """Increment usage count when template is instantiated"""
        self.usage_count = (self.usage_count or 0) + 1
    
    def get_phase_count(self):
        """Get number of phases in this template"""
        data = self.get_template_data()
        return len(data.get('phases', []))
    
    def get_task_count(self):
        """Get total number of tasks across all phases"""
        data = self.get_template_data()
        total_tasks = 0
        for phase in data.get('phases', []):
            total_tasks += len(phase.get('tasks', []))
        return total_tasks
    
    def get_summary(self):
        """Get a summary of the template for display"""
        return {
            'phase_count': self.get_phase_count(),
            'task_count': self.get_task_count(),
            'estimated_duration_days': self.estimated_duration_days or 0,
            'category': self.category or 'General',
            'usage_count': self.usage_count or 0
        }