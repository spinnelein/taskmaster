"""
Project schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base_schemas import BaseResponse

class ProjectPhaseCreate(BaseModel):
    """Schema for creating a project phase"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    order: int = Field(..., ge=0)
    estimated_start_date: Optional[datetime] = None
    estimated_end_date: Optional[datetime] = None
    depends_on_phase_ids: Optional[List[str]] = None

class ProjectPhaseUpdate(BaseModel):
    """Schema for updating a project phase"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    order: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    estimated_start_date: Optional[datetime] = None
    estimated_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    depends_on_phase_ids: Optional[List[str]] = None

class ProjectPhaseResponse(BaseResponse):
    """Schema for project phase response"""
    title: str
    description: Optional[str]
    order: int
    status: str
    estimated_start_date: Optional[datetime]
    estimated_end_date: Optional[datetime]
    actual_start_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    depends_on_phase_ids: Optional[List[str]]
    project_id: str
    
    class Config:
        orm_mode = True

class ProjectCreate(BaseModel):
    """Schema for creating a project"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    priority: str = Field("medium")
    estimated_start_date: Optional[datetime] = None
    estimated_end_date: Optional[datetime] = None
    initiative_id: Optional[str] = None
    template_id: Optional[str] = None
    tags: Optional[List[str]] = None
    phases: Optional[List[ProjectPhaseCreate]] = None
    
    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ["low", "medium", "high", "critical"]
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v

class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_start_date: Optional[datetime] = None
    estimated_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    initiative_id: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["planning", "active", "on_hold", "completed", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of {valid_statuses}")
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v is not None:
            valid_priorities = ["low", "medium", "high", "critical"]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of {valid_priorities}")
        return v

class ProjectResponse(BaseResponse):
    """Schema for project response"""
    title: str
    description: Optional[str]
    status: str
    priority: str
    estimated_start_date: Optional[datetime]
    estimated_end_date: Optional[datetime]
    actual_start_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    initiative_id: Optional[str]
    template_id: Optional[str]
    tags: Optional[List[str]]
    custom_fields: Optional[Dict[str, Any]]
    phases: List[ProjectPhaseResponse]
    
    class Config:
        orm_mode = True

class ProjectListResponse(BaseModel):
    """Schema for list of projects"""
    projects: List[ProjectResponse]
    total: int

class ProjectTemplateCreate(BaseModel):
    """Schema for creating a project template"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field("personal")
    phases_template: Optional[List[Dict[str, Any]]] = None
    tasks_template: Optional[List[Dict[str, Any]]] = None
    events_template: Optional[List[Dict[str, Any]]] = None
    execution_script: Optional[str] = None
    default_settings: Optional[Dict[str, Any]] = None
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = ["personal", "work", "home", "creative", "learning", "health", "custom"]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of {valid_categories}")
        return v

class ProjectTemplateResponse(BaseResponse):
    """Schema for project template response"""
    title: str
    description: Optional[str]
    category: str
    version: str
    is_public: bool
    usage_count: int
    phases_template: Optional[List[Dict[str, Any]]]
    tasks_template: Optional[List[Dict[str, Any]]]
    events_template: Optional[List[Dict[str, Any]]]
    execution_script: Optional[str]
    default_settings: Optional[Dict[str, Any]]
    
    class Config:
        orm_mode = True

class ExecuteProjectTemplate(BaseModel):
    """Schema for executing a project template"""
    template_id: str
    project_title: str = Field(..., min_length=1, max_length=255)
    start_date: Optional[datetime] = None
    execution_parameters: Optional[Dict[str, Any]] = None