"""
Task API routes
NO EMOJIS
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from ...schemas.task_schemas import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from ...schemas.base_schemas import MessageResponse
from ...data.repositories.task_repo import TaskRepository
from ...domain.task import Task
from ..dependencies import get_db

router = APIRouter(tags=["tasks"])

@router.get("", response_model=TaskListResponse)
def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get all tasks with optional status filter"""
    repo = TaskRepository(db)
    
    if status:
        tasks = repo.get_by_status(status)
    else:
        tasks = repo.get_all()
    
    return TaskListResponse(
        tasks=[TaskResponse(**task.to_dict()) for task in tasks],
        total=len(tasks)
    )

@router.post("", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new task"""
    repo = TaskRepository(db)
    
    try:
        task = Task(
            title=task_data.title,
            duration=task_data.duration,
            urgency=task_data.urgency,
            description=task_data.description,
            status=task_data.status,
            due_date=task_data.due_date,
            due_time=task_data.due_time
        )
        saved_task = repo.save(task)
        return TaskResponse(**saved_task.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/overdue", response_model=TaskListResponse)
def get_overdue_tasks(db: Session = Depends(get_db)):
    """Get all overdue tasks"""
    repo = TaskRepository(db)
    tasks = repo.get_overdue()
    
    return TaskListResponse(
        tasks=[TaskResponse(**task.to_dict()) for task in tasks],
        total=len(tasks)
    )

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific task by ID"""
    repo = TaskRepository(db)
    task = repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(**task.to_dict())

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task"""
    repo = TaskRepository(db)
    task = repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields if provided
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    try:
        task.validate()
        saved_task = repo.save(task)
        return TaskResponse(**saved_task.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Delete a task"""
    repo = TaskRepository(db)
    
    if not repo.get_by_id(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    deleted = repo.delete(task_id)
    
    if deleted:
        return MessageResponse(message="Task deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete task")

@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Mark a task as completed"""
    repo = TaskRepository(db)
    task = repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        task.complete()
        saved_task = repo.save(task)
        return TaskResponse(**saved_task.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))