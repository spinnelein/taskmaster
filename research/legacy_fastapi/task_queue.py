"""
Task Queue API routes
NO EMOJIS
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import date, datetime

from ...data.database import get_db
from ...services.task_queue_service import TaskQueueService
from ...schemas.schedule_schemas_enhanced import (
    TaskQueueRequest, TaskQueueResponse, TaskQueueItem,
    SnoozeTaskRequest, PartialCompleteRequest
)

router = APIRouter(prefix="/task-queue", tags=["task-queue"])

@router.get("/", response_model=TaskQueueResponse)
def get_task_queue(
    include_blocked: bool = False,
    include_snoozed: bool = False,
    date_range_start: Optional[date] = None,
    date_range_end: Optional[date] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get prioritized task queue"""
    try:
        task_queue_service = TaskQueueService(db)
        
        task_queue_items = task_queue_service.get_task_queue(
            include_blocked=include_blocked,
            include_snoozed=include_snoozed,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            limit=limit
        )
        
        # Convert to response format
        queue_items = []
        blocked_count = 0
        snoozed_count = 0
        
        for item in task_queue_items:
            if not item["can_be_scheduled"]:
                blocked_count += 1
            
            if item["task"].snoozed_until and item["task"].snoozed_until > datetime.now():
                snoozed_count += 1
            
            queue_items.append(TaskQueueItem(
                task=item["task"],
                priority_score=item["priority_score"],
                is_overdue=item["is_overdue"],
                days_overdue=item["days_overdue"],
                can_be_scheduled=item["can_be_scheduled"],
                blocking_reasons=item["blocking_reasons"]
            ))
        
        return TaskQueueResponse(
            unscheduled_tasks=queue_items,
            total_unscheduled=len(queue_items),
            blocked_count=blocked_count,
            snoozed_count=snoozed_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching task queue: {str(e)}"
        )

@router.get("/next")
def get_next_task(
    exclude_task_ids: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get the next highest priority task"""
    try:
        task_queue_service = TaskQueueService(db)
        
        exclude_list = []
        if exclude_task_ids:
            exclude_list = exclude_task_ids.split(",")
        
        next_task = task_queue_service.get_next_task(exclude_task_ids=exclude_list)
        
        if not next_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No suitable tasks found"
            )
        
        return {
            "task": next_task["task"],
            "priority_score": next_task["priority_score"],
            "is_overdue": next_task["is_overdue"],
            "days_overdue": next_task["days_overdue"],
            "blocking_reasons": next_task["blocking_reasons"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting next task: {str(e)}"
        )

@router.post("/tasks/{task_id}/snooze")
def snooze_task(
    task_id: str,
    snooze_request: SnoozeTaskRequest,
    db: Session = Depends(get_db)
):
    """Snooze a task for specified minutes"""
    try:
        task_queue_service = TaskQueueService(db)
        
        # Calculate minutes from snooze_until
        from datetime import datetime, timedelta
        now = datetime.now()
        snooze_minutes = int((snooze_request.snooze_until - now).total_seconds() / 60)
        
        if snooze_minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Snooze time must be in the future"
            )
        
        success = task_queue_service.snooze_task(task_id, snooze_minutes, snooze_request.reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or could not be snoozed"
            )
        
        return {
            "message": f"Task snoozed for {snooze_minutes} minutes",
            "snooze_until": snooze_request.snooze_until
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error snoozing task: {str(e)}"
        )

@router.post("/tasks/{task_id}/snooze-minutes")
def snooze_task_by_minutes(
    task_id: str,
    minutes: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Snooze a task for specified number of minutes"""
    try:
        if minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minutes must be positive"
            )
        
        task_queue_service = TaskQueueService(db)
        success = task_queue_service.snooze_task(task_id, minutes)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or could not be snoozed"
            )
        
        return {
            "message": f"Task snoozed for {minutes} minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error snoozing task: {str(e)}"
        )

@router.post("/tasks/{task_id}/partial-complete")
def add_partial_completion(
    task_id: str,
    completion_request: PartialCompleteRequest,
    db: Session = Depends(get_db)
):
    """Add partial completion to a task"""
    try:
        task_queue_service = TaskQueueService(db)
        
        success = task_queue_service.add_partial_completion(
            task_id,
            completion_request.minutes_worked,
            completion_request.notes
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or could not update completion"
            )
        
        return {
            "message": f"Added {completion_request.minutes_worked} minutes to task",
            "minutes_worked": completion_request.minutes_worked
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding partial completion: {str(e)}"
        )

@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Mark a task as completed"""
    try:
        task_queue_service = TaskQueueService(db)
        
        success = task_queue_service.complete_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or could not be completed"
            )
        
        return {
            "message": "Task completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing task: {str(e)}"
        )

@router.get("/statistics")
def get_queue_statistics(
    db: Session = Depends(get_db)
):
    """Get task queue statistics"""
    try:
        task_queue_service = TaskQueueService(db)
        stats = task_queue_service.get_queue_statistics()
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting queue statistics: {str(e)}"
        )

@router.get("/priority-scores/{task_id}")
def get_task_priority_score(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get priority score for a specific task"""
    try:
        from ...data.repositories.task_repo import TaskRepository
        
        task_repo = TaskRepository(db)
        task = task_repo.get(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task_queue_service = TaskQueueService(db)
        priority_score = task_queue_service.calculate_priority_score(task)
        
        return {
            "task_id": task_id,
            "priority_score": priority_score,
            "urgency": task.urgency,
            "due_date": task.due_date,
            "is_overdue": task.due_date and task.due_date < date.today() if task.due_date else False,
            "is_recurring": task.is_recurring,
            "has_partial_completion": bool(task.partial_completion_minutes),
            "is_snoozed": bool(task.snoozed_until and task.snoozed_until > datetime.now())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating priority score: {str(e)}"
        )