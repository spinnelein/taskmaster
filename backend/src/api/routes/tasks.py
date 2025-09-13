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
from ...data.models.task_model import TaskStatus
from ..dependencies import get_db

router = APIRouter(tags=["tasks"])

@router.get("/test-fix")
def test_fix():
    """Test endpoint to verify server has updated code"""
    return {"message": "Server has the updated code with get() method fix", "status": "fixed"}

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
    
    # Convert tasks to response format
    task_responses = []
    for task in tasks:
        try:
            # Convert SQLAlchemy model to dict with enum handling
            task_dict = {
                'id': task.id,
                'created_at': task.created_at,
                'updated_at': task.updated_at,
                'title': task.title,
                'duration': task.duration,
                'urgency': task.urgency,
                'priority': task.priority.value if task.priority else 'medium',
                'description': task.description or '',
                'status': task.status.value if task.status else 'active',
                'due_date': task.due_date,
                'due_time': task.due_time,
                'is_completed': task.is_completed or False,
                
                # Enhanced fields
                'is_divisible': task.is_divisible or False,
                'min_chunk_size': task.min_chunk_size,
                'required_weather': task.required_weather.value if task.required_weather else 'any',
                'required_context': task.required_context,
                'equipment_needed': task.equipment_needed,
                'depends_on_task_ids': task.depends_on_task_ids,
                'blocks_task_ids': task.blocks_task_ids,
                
                # Organization
                'initiative_id': task.initiative_id,
                'project_id': task.project_id,
                'phase_id': task.phase_id,
                'meal_id': task.meal_id,
                
                # Queue management
                'queue_position': task.queue_position,
                'auto_scheduled': task.auto_scheduled or False,
                
                # Cost tracking
                'estimated_cost': task.estimated_cost,
                'actual_cost': task.actual_cost,
                
                # Recurring task
                'is_recurring': task.is_recurring or False,
                'recurrence_pattern': task.recurrence_pattern,
                'parent_task_id': task.parent_task_id,
                'last_completed_at': task.last_completed_at,
                
                # Progress tracking
                'partial_completion_minutes': task.partial_completion_minutes or 0,
                'remaining_minutes': task.remaining_minutes,
                
                # Snooze
                'is_snoozed': task.is_snoozed or False,
                'snoozed_until': task.snoozed_until,
            }
            
            task_responses.append(TaskResponse.model_validate(task_dict))
        except Exception as e:
            # Skip tasks that can't be serialized for now
            continue
    
    return TaskListResponse(
        tasks=task_responses,
        total=len(task_responses)
    )

@router.post("", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new task"""
    repo = TaskRepository(db)
    
    try:
        # Convert task data to dict for repository
        task_dict = {
            'title': task_data.title,
            'duration': task_data.duration,
            'urgency': task_data.urgency,
            'description': task_data.description,
            'status': task_data.status.upper() if task_data.status else 'ACTIVE',
            'due_date': task_data.due_date,
            'due_time': task_data.due_time
        }
        
        saved_task = repo.create(task_dict)
        
        # Convert to response format with enum handling
        task_response_dict = {
            'id': saved_task.id,
            'created_at': saved_task.created_at,
            'updated_at': saved_task.updated_at,
            'title': saved_task.title,
            'duration': saved_task.duration,
            'urgency': saved_task.urgency,
            'priority': saved_task.priority.value if saved_task.priority else 'medium',
            'description': saved_task.description or '',
            'status': saved_task.status.value if saved_task.status else 'active',
            'due_date': saved_task.due_date,
            'due_time': saved_task.due_time,
            'is_completed': saved_task.is_completed or False,
            
            # Enhanced fields
            'is_divisible': saved_task.is_divisible or False,
            'min_chunk_size': saved_task.min_chunk_size,
            'required_weather': saved_task.required_weather.value if saved_task.required_weather else 'any',
            'required_context': saved_task.required_context,
            'equipment_needed': saved_task.equipment_needed,
            'depends_on_task_ids': saved_task.depends_on_task_ids,
            'blocks_task_ids': saved_task.blocks_task_ids,
            
            # Organization
            'initiative_id': saved_task.initiative_id,
            'project_id': saved_task.project_id,
            'phase_id': saved_task.phase_id,
            'meal_id': saved_task.meal_id,
            
            # Queue management
            'queue_position': saved_task.queue_position,
            'auto_scheduled': saved_task.auto_scheduled or False,
            
            # Cost tracking
            'estimated_cost': saved_task.estimated_cost,
            'actual_cost': saved_task.actual_cost,
            
            # Recurring task
            'is_recurring': saved_task.is_recurring or False,
            'recurrence_pattern': saved_task.recurrence_pattern,
            'parent_task_id': saved_task.parent_task_id,
            'last_completed_at': saved_task.last_completed_at,
            
            # Progress tracking
            'partial_completion_minutes': saved_task.partial_completion_minutes or 0,
            'remaining_minutes': saved_task.remaining_minutes,
            
            # Snooze
            'is_snoozed': saved_task.is_snoozed or False,
            'snoozed_until': saved_task.snoozed_until,
        }
        
        return TaskResponse.model_validate(task_response_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

@router.get("/overdue", response_model=TaskListResponse)
def get_overdue_tasks(db: Session = Depends(get_db)):
    """Get all overdue tasks"""
    repo = TaskRepository(db)
    tasks = repo.get_overdue()
    
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(task) for task in tasks],
        total=len(tasks)
    )

@router.get("/{task_id}")
def get_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific task by ID"""
    repo = TaskRepository(db)
    task = repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Return simple dict instead of TaskResponse to avoid schema issues
    return task.to_dict()

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task"""
    repo = TaskRepository(db)
    task = repo.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Convert update data to dict, excluding unset fields
    update_data = task_data.model_dump(exclude_unset=True)
    
    # Convert status to uppercase for enum compatibility if provided
    if 'status' in update_data:
        update_data['status'] = update_data['status'].upper()
    
    # Convert priority to uppercase for enum compatibility if provided  
    if 'priority' in update_data:
        update_data['priority'] = update_data['priority'].upper()
    
    # Convert weather to uppercase for enum compatibility if provided
    if 'required_weather' in update_data:
        update_data['required_weather'] = update_data['required_weather'].upper()
    
    try:
        # Use repository update method
        updated_task = repo.update(task_id, update_data)
        
        if not updated_task:
            raise HTTPException(status_code=500, detail="Failed to update task")
        
        # Convert to response format with enum handling
        task_dict = {
            'id': updated_task.id,
            'created_at': updated_task.created_at,
            'updated_at': updated_task.updated_at,
            'title': updated_task.title,
            'duration': updated_task.duration,
            'urgency': updated_task.urgency,
            'priority': updated_task.priority.value if updated_task.priority else 'medium',
            'description': updated_task.description or '',
            'status': updated_task.status.value if updated_task.status else 'active',
            'due_date': updated_task.due_date,
            'due_time': updated_task.due_time,
            'is_completed': updated_task.is_completed or False,
            
            # Enhanced fields
            'is_divisible': updated_task.is_divisible or False,
            'min_chunk_size': updated_task.min_chunk_size,
            'required_weather': updated_task.required_weather.value if updated_task.required_weather else 'any',
            'required_context': updated_task.required_context,
            'equipment_needed': updated_task.equipment_needed,
            'depends_on_task_ids': updated_task.depends_on_task_ids,
            'blocks_task_ids': updated_task.blocks_task_ids,
            
            # Organization
            'initiative_id': updated_task.initiative_id,
            'project_id': updated_task.project_id,
            'phase_id': updated_task.phase_id,
            'meal_id': updated_task.meal_id,
            
            # Queue management
            'queue_position': updated_task.queue_position,
            'auto_scheduled': updated_task.auto_scheduled or False,
            
            # Cost tracking
            'estimated_cost': updated_task.estimated_cost,
            'actual_cost': updated_task.actual_cost,
            
            # Recurring task
            'is_recurring': updated_task.is_recurring or False,
            'recurrence_pattern': updated_task.recurrence_pattern,
            'parent_task_id': updated_task.parent_task_id,
            'last_completed_at': updated_task.last_completed_at,
            
            # Progress tracking
            'partial_completion_minutes': updated_task.partial_completion_minutes or 0,
            'remaining_minutes': updated_task.remaining_minutes,
            
            # Snooze
            'is_snoozed': updated_task.is_snoozed or False,
            'snoozed_until': updated_task.snoozed_until,
        }
        
        return TaskResponse.model_validate(task_dict)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")

@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Delete a task"""
    repo = TaskRepository(db)
    
    if not repo.get(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    deleted = repo.delete(task_id)
    
    if deleted:
        return MessageResponse(message="Task deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete task")

@router.post("/{task_id}/complete")
def complete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Mark a task as completed"""
    repo = TaskRepository(db)
    task = repo.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Update task status to completed using repository pattern
        update_data = {
            "status": TaskStatus.COMPLETED,
            "is_completed": True
        }
        updated_task = repo.update(task_id, update_data)
        
        if not updated_task:
            raise HTTPException(status_code=500, detail="Failed to update task")
            
        # Return a simple success message for now
        return {"message": "Task completed successfully", "task_id": task_id, "status": "completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing task: {str(e)}")