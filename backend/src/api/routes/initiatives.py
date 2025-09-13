"""
Initiative API routes
NO EMOJIS
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from ...data.database import get_db
from ...data.repositories.initiative_repo import InitiativeRepository
from ...schemas.initiative_schemas import (
    InitiativeCreate, InitiativeUpdate, InitiativeResponse, 
    InitiativeListResponse, InitiativeStats
)

router = APIRouter()

def get_initiative_repo(db: Session = Depends(get_db)) -> InitiativeRepository:
    return InitiativeRepository(db)

@router.post("/", response_model=InitiativeResponse, status_code=status.HTTP_201_CREATED)
def create_initiative(
    initiative: InitiativeCreate,
    repo: InitiativeRepository = Depends(get_initiative_repo)
):
    """Create a new initiative"""
    try:
        new_initiative = repo.create(initiative.model_dump())
        if not new_initiative:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create initiative"
            )
        return new_initiative.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=InitiativeListResponse)
def get_initiatives(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    repo: InitiativeRepository = Depends(get_initiative_repo)
):
    """Get all initiatives"""
    try:
        if active_only:
            initiatives = repo.get_active()
        else:
            initiatives = repo.get_all()
        
        # Apply pagination
        total = len(initiatives)
        initiatives = initiatives[skip:skip + limit]
        
        return InitiativeListResponse(
            initiatives=[init.to_dict() for init in initiatives],
            total=total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/templates", response_model=InitiativeListResponse)
def get_initiative_templates(
    repo: InitiativeRepository = Depends(get_initiative_repo)
):
    """Get all initiative templates"""
    try:
        templates = repo.get_templates()
        return InitiativeListResponse(
            initiatives=[tmpl.to_dict() for tmpl in templates],
            total=len(templates)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/templates/{template_id}/create", response_model=InitiativeResponse)
def create_from_template(
    template_id: str,
    title: str,
    repo: InitiativeRepository = Depends(get_initiative_repo)
):
    """Create a new initiative from a template"""
    try:
        initiative = repo.create_from_template(template_id, title)
        if not initiative:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        return initiative.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{initiative_id}", response_model=InitiativeResponse)
def get_initiative(
    initiative_id: str,
    repo: InitiativeRepository = Depends(get_initiative_repo)
):
    """Get a specific initiative"""
    initiative = repo.get(initiative_id)
    if not initiative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Initiative not found"
        )
    return initiative.to_dict()

@router.get("/{initiative_id}/stats", response_model=InitiativeStats)
def get_initiative_stats(
    initiative_id: str,
    repo: InitiativeRepository = Depends(get_initiative_repo)
):
    """Get initiative statistics"""
    try:
        stats_data = repo.get_with_stats(initiative_id)
        if not stats_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Initiative not found"
            )
        
        # Get all tasks for this initiative to calculate missing fields
        from ...data.models.task_model import TaskModel
        tasks = repo.db.query(TaskModel).filter(
            TaskModel.initiative_id == initiative_id
        ).all()
        
        # Calculate status breakdown
        active_tasks = len([t for t in tasks if t.status.value == "active"])
        blocked_tasks = len([t for t in tasks if t.status.value == "blocked"])
        
        return InitiativeStats(
            initiative_id=initiative_id,
            total_tasks=stats_data["stats"]["total_tasks"],
            active_tasks=active_tasks,
            completed_tasks=stats_data["stats"]["completed_tasks"],
            blocked_tasks=blocked_tasks,
            completion_rate=stats_data["stats"]["completion_rate"],
            last_completed_at=stats_data["stats"]["last_completed_at"],
            average_task_duration_minutes=stats_data["stats"]["average_duration_minutes"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{initiative_id}", response_model=InitiativeResponse)
def update_initiative(
    initiative_id: str,
    initiative: InitiativeUpdate,
    repo: InitiativeRepository = Depends(get_initiative_repo)
):
    """Update an initiative"""
    existing = repo.get(initiative_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Initiative not found"
        )
    
    try:
        updated = repo.update(initiative_id, initiative.model_dump(exclude_unset=True))
        return updated.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{initiative_id}/complete", response_model=InitiativeResponse)
def complete_initiative(
    initiative_id: str,
    repo: InitiativeRepository = Depends(get_initiative_repo)
):
    """Complete an initiative and all its tasks"""
    existing = repo.get(initiative_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Initiative not found"
        )
    
    if existing.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initiative is already completed"
        )
    
    try:
        completed = repo.complete_initiative_with_tasks(initiative_id)
        return completed.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{initiative_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_initiative(
    initiative_id: str,
    repo: InitiativeRepository = Depends(get_initiative_repo)
):
    """Delete an initiative"""
    existing = repo.get(initiative_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Initiative not found"
        )
    
    try:
        repo.delete(initiative_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )