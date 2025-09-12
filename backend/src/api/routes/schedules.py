"""
Schedule API routes
NO EMOJIS
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from ...data.database import get_db
from ...data.repositories.schedule_repo import ScheduleRepository
from ...schemas.schedule_schemas_enhanced import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    ScheduleGenerateRequest, TaskQueueRequest, TaskQueueResponse,
    TaskScheduleCreate, TaskScheduleResponse,
    SnoozeTaskRequest, PartialCompleteRequest
)

router = APIRouter()

def get_schedule_repo(db: Session = Depends(get_db)) -> ScheduleRepository:
    return ScheduleRepository(db)

@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    schedule: ScheduleCreate,
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Create a new schedule"""
    try:
        # Calculate week end date
        week_end = schedule.week_start_date + timedelta(days=6)
        
        schedule_data = schedule.dict()
        schedule_data["week_end_date"] = week_end
        
        new_schedule = repo.create(schedule_data)
        if not new_schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create schedule"
            )
        
        return repo.get_with_pools(new_schedule.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/current", response_model=ScheduleResponse)
def get_current_schedule(
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Get the current week's schedule"""
    schedule = repo.get_current_week()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current schedule found"
        )
    return repo.get_with_pools(schedule.id)

@router.get("/week/{week_start_date}", response_model=ScheduleResponse)
def get_schedule_by_week(
    week_start_date: date,
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Get schedule for a specific week"""
    schedule = repo.get_by_week(week_start_date)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found for this week"
        )
    return repo.get_with_pools(schedule.id)

@router.post("/generate", response_model=ScheduleResponse)
def generate_schedule(
    request: ScheduleGenerateRequest,
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Generate or regenerate a weekly schedule"""
    try:
        # Use current week if not specified
        if request.week_start_date is None:
            today = datetime.now().date()
            # Calculate Monday of current week
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
        else:
            week_start = request.week_start_date
        
        # Get or create schedule
        schedule = repo.get_by_week(week_start)
        if not schedule:
            week_end = week_start + timedelta(days=6)
            schedule = repo.create({
                "week_start_date": week_start,
                "week_end_date": week_end,
                "is_current": True
            })
        
        # Generate time pools from events
        if request.regenerate_pools:
            time_pools = repo.create_time_pools_from_events(schedule.id)
        
        # Auto-schedule tasks
        if request.auto_schedule_tasks:
            scheduled_tasks = repo.auto_schedule_tasks(schedule.id)
        
        # Mark as generated
        schedule.generated_at = datetime.utcnow()
        repo.db.commit()
        
        return repo.get_with_pools(schedule.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/queue/unscheduled", response_model=TaskQueueResponse)
def get_unscheduled_tasks(
    limit: int = Query(100, ge=1, le=500),
    include_blocked: bool = Query(False),
    include_snoozed: bool = Query(False),
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Get prioritized queue of unscheduled tasks"""
    try:
        task_queue = repo.get_unscheduled_tasks(limit)
        
        # Filter based on parameters
        if not include_blocked:
            task_queue = [t for t in task_queue if t["can_be_scheduled"]]
        
        if not include_snoozed:
            task_queue = [t for t in task_queue if not t["task"].is_snoozed]
        
        # Calculate counts
        total_unscheduled = len(task_queue)
        blocked_count = len([t for t in task_queue if not t["can_be_scheduled"]])
        snoozed_count = len([t for t in task_queue if t["task"].is_snoozed])
        
        return TaskQueueResponse(
            unscheduled_tasks=task_queue,
            total_unscheduled=total_unscheduled,
            blocked_count=blocked_count,
            snoozed_count=snoozed_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/schedule-task", response_model=TaskScheduleResponse)
def schedule_task(
    task_schedule: TaskScheduleCreate,
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Schedule a specific task into a time pool"""
    try:
        scheduled_task = repo.schedule_task(
            task_schedule.task_id,
            task_schedule.time_pool_id,
            task_schedule.scheduled_duration_minutes
        )
        
        if not scheduled_task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to schedule task - task or time pool not found, or insufficient time"
            )
        
        return scheduled_task
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/auto-schedule/{schedule_id}")
def auto_schedule_tasks(
    schedule_id: str,
    max_tasks: int = Query(50, ge=1, le=100),
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Automatically schedule tasks into available time pools"""
    try:
        scheduled_tasks = repo.auto_schedule_tasks(schedule_id, max_tasks)
        
        return {
            "message": f"Successfully scheduled {len(scheduled_tasks)} tasks",
            "scheduled_tasks": len(scheduled_tasks),
            "task_ids": [task.task_id for task in scheduled_tasks]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: str,
    schedule: ScheduleUpdate,
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Update a schedule"""
    existing = repo.get(schedule_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    try:
        updated = repo.update(schedule_id, schedule.dict(exclude_unset=True))
        return repo.get_with_pools(updated.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Task management routes
@router.post("/tasks/{task_id}/snooze")
def snooze_task(
    task_id: str,
    snooze_request: SnoozeTaskRequest,
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Snooze an overdue task"""
    try:
        from ...data.models.task_model import TaskModel
        
        task = repo.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task.is_snoozed = True
        task.snoozed_until = snooze_request.snooze_until
        repo.db.commit()
        
        return {"message": "Task snoozed successfully", "snoozed_until": task.snoozed_until}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/tasks/{task_id}/partial-complete")
def mark_partial_complete(
    task_id: str,
    completion_request: PartialCompleteRequest,
    repo: ScheduleRepository = Depends(get_schedule_repo)
):
    """Mark partial completion of a task"""
    try:
        from ...data.models.task_model import TaskModel
        
        task = repo.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Update partial completion
        task.partial_completion_minutes += completion_request.minutes_worked
        
        # Calculate remaining time
        if task.remaining_minutes:
            task.remaining_minutes = max(0, task.remaining_minutes - completion_request.minutes_worked)
        else:
            task.remaining_minutes = max(0, task.duration - task.partial_completion_minutes)
        
        # Mark as completed if fully done
        if task.remaining_minutes == 0:
            task.status = "completed"
            task.last_completed_at = datetime.utcnow()
        
        repo.db.commit()
        
        return {
            "message": "Partial completion recorded",
            "minutes_worked": completion_request.minutes_worked,
            "total_completed": task.partial_completion_minutes,
            "remaining_minutes": task.remaining_minutes,
            "is_completed": task.remaining_minutes == 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )