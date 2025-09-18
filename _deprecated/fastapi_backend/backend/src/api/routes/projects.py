"""
Project API routes
NO EMOJIS
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from ...data.database import get_db
from ...data.repositories.project_repo import ProjectRepository
from ...schemas.project_schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    ProjectPhaseCreate, ProjectPhaseUpdate, ProjectPhaseResponse,
    ProjectTemplateCreate, ProjectTemplateResponse, ExecuteProjectTemplate
)

router = APIRouter()

def get_project_repo(db: Session = Depends(get_db)) -> ProjectRepository:
    return ProjectRepository(db)

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    repo: ProjectRepository = Depends(get_project_repo)
):
    """Create a new project"""
    try:
        project_data = project.model_dump(exclude={"phases"})
        new_project = repo.create(project_data)
        
        if not new_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create project"
            )
        
        # Create phases if provided
        if project.phases:
            for phase_data in project.phases:
                repo.create_phase(new_project.id, phase_data.model_dump())
        
        # Return project with phases
        project_with_phases = repo.get_with_phases(new_project.id)
        return project_with_phases.to_dict() if project_with_phases else None
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=ProjectListResponse)
def get_projects(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    initiative_id: str = None,
    repo: ProjectRepository = Depends(get_project_repo)
):
    """Get all projects"""
    try:
        if initiative_id:
            projects = repo.get_by_initiative(initiative_id)
        elif status_filter:
            from ...data.models.project_model import ProjectStatus
            status_enum = ProjectStatus(status_filter)
            projects = repo.get_by_status(status_enum)
        else:
            projects = repo.get_all()
        
        # Apply pagination
        total = len(projects)
        projects = projects[skip:skip + limit]
        
        return ProjectListResponse(
            projects=[project.to_dict() for project in projects],
            total=total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repo)
):
    """Get a specific project with phases"""
    project = repo.get_with_phases(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project.to_dict()

@router.get("/{project_id}/stats")
def get_project_stats(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repo)
):
    """Get project statistics"""
    try:
        stats = repo.get_project_stats(project_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    project: ProjectUpdate,
    repo: ProjectRepository = Depends(get_project_repo)
):
    """Update a project"""
    existing = repo.get(project_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        updated = repo.update(project_id, project.model_dump(exclude_unset=True))
        updated_with_phases = repo.get_with_phases(updated.id)
        return updated_with_phases.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repo)
):
    """Delete a project"""
    existing = repo.get(project_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        repo.delete(project_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Phase management routes
@router.post("/{project_id}/phases", response_model=ProjectPhaseResponse, status_code=status.HTTP_201_CREATED)
def create_phase(
    project_id: str,
    phase: ProjectPhaseCreate,
    repo: ProjectRepository = Depends(get_project_repo)
):
    """Create a new phase for a project"""
    try:
        new_phase = repo.create_phase(project_id, phase.model_dump())
        if not new_phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        return new_phase.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/phases/{phase_id}", response_model=ProjectPhaseResponse)
def update_phase(
    phase_id: str,
    phase: ProjectPhaseUpdate,
    repo: ProjectRepository = Depends(get_project_repo)
):
    """Update a project phase"""
    try:
        # If status is being updated, use the special method
        if phase.status:
            from ...data.models.project_model import ProjectStatus
            status_enum = ProjectStatus(phase.status)
            updated_phase = repo.update_phase_status(phase_id, status_enum)
        else:
            # Standard update using repository method
            updated_phase = repo.update_phase(phase_id, phase.model_dump(exclude_unset=True))
        
        if not updated_phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Phase not found"
            )
        
        return updated_phase.to_dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Template execution
@router.post("/templates/execute", response_model=ProjectResponse)
def execute_project_template(
    template_execution: ExecuteProjectTemplate,
    repo: ProjectRepository = Depends(get_project_repo)
):
    """Execute a project template to create a new project"""
    try:
        project = repo.execute_template(
            template_execution.template_id,
            template_execution.project_title,
            template_execution.start_date,
            template_execution.execution_parameters
        )
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or execution failed"
            )
        
        project_with_phases = repo.get_with_phases(project.id)
        return project_with_phases.to_dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )