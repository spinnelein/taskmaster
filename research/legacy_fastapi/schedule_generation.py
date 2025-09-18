"""
Schedule Generation API routes
NO EMOJIS
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import date

from ...data.database import get_db
from ...services.schedule_generation_service import ScheduleGenerationService
from ...schemas.schedule_schemas_enhanced import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    ScheduleGenerateRequest, TimePoolResponse, TaskScheduleResponse
)

router = APIRouter(prefix="/schedule-generation", tags=["schedule-generation"])

@router.post("/generate-weekly", response_model=ScheduleResponse)
def generate_weekly_schedule(
    request: ScheduleGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate a complete weekly schedule with time pools"""
    try:
        schedule_service = ScheduleGenerationService(db)
        
        schedule = schedule_service.generate_weekly_schedule(
            week_start_date=request.week_start_date,
            regenerate_if_exists=request.regenerate_pools
        )
        
        # Auto-schedule tasks if requested
        if request.auto_schedule_tasks:
            scheduled_tasks = schedule_service.auto_schedule_tasks(
                schedule.id,
                max_tasks=50,
                allow_partial_scheduling=True
            )
            print(f"Auto-scheduled {len(scheduled_tasks)} tasks")
        
        return schedule
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating schedule: {str(e)}"
        )

@router.post("/schedules/{schedule_id}/time-pools")
def generate_time_pools(
    schedule_id: str,
    db: Session = Depends(get_db)
):
    """Generate time pools from blocking events for a schedule"""
    try:
        schedule_service = ScheduleGenerationService(db)
        
        time_pools = schedule_service.generate_time_pools_from_events(schedule_id)
        
        return {
            "message": f"Generated {len(time_pools)} time pools",
            "schedule_id": schedule_id,
            "time_pools_created": len(time_pools)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating time pools: {str(e)}"
        )

@router.post("/schedules/{schedule_id}/auto-schedule")
def auto_schedule_tasks(
    schedule_id: str,
    max_tasks: int = Body(50, embed=True),
    allow_partial: bool = Body(True, embed=True),
    db: Session = Depends(get_db)
):
    """Auto-schedule tasks into available time pools"""
    try:
        schedule_service = ScheduleGenerationService(db)
        
        scheduled_tasks = schedule_service.auto_schedule_tasks(
            schedule_id,
            max_tasks=max_tasks,
            allow_partial_scheduling=allow_partial
        )
        
        return {
            "message": f"Auto-scheduled {len(scheduled_tasks)} task sessions",
            "schedule_id": schedule_id,
            "scheduled_task_count": len(scheduled_tasks),
            "task_sessions": [
                {
                    "task_id": ts.task_id,
                    "scheduled_start": ts.scheduled_start,
                    "scheduled_end": ts.scheduled_end,
                    "duration_minutes": ts.scheduled_duration_minutes,
                    "is_partial": ts.is_partial
                } for ts in scheduled_tasks
            ]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error auto-scheduling tasks: {str(e)}"
        )

@router.post("/regenerate-current")
def regenerate_current_schedule(
    db: Session = Depends(get_db)
):
    """Regenerate the current week's schedule"""
    try:
        schedule_service = ScheduleGenerationService(db)
        
        schedule = schedule_service.regenerate_current_schedule()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No current schedule found to regenerate"
            )
        
        return {
            "message": "Current schedule regenerated successfully",
            "schedule": schedule
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error regenerating schedule: {str(e)}"
        )

@router.get("/schedules/{schedule_id}/summary")
def get_schedule_summary(
    schedule_id: str,
    db: Session = Depends(get_db)
):
    """Get a summary of schedule utilization and statistics"""
    try:
        schedule_service = ScheduleGenerationService(db)
        
        summary = schedule_service.get_schedule_summary(schedule_id)
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting schedule summary: {str(e)}"
        )

@router.get("/current-schedule/summary")
def get_current_schedule_summary(
    db: Session = Depends(get_db)
):
    """Get summary of the current active schedule"""
    try:
        from ...data.repositories.schedule_repo import ScheduleRepository
        
        schedule_repo = ScheduleRepository(db)
        current_schedule = schedule_repo.get_current_schedule()
        
        if not current_schedule:
            return {
                "message": "No current schedule found",
                "has_current_schedule": False
            }
        
        schedule_service = ScheduleGenerationService(db)
        summary = schedule_service.get_schedule_summary(current_schedule.id)
        
        return {
            "has_current_schedule": True,
            **summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting current schedule summary: {str(e)}"
        )

@router.post("/quick-schedule")
def quick_schedule_setup(
    week_start: Optional[date] = Body(None),
    work_start: str = Body("09:00:00"),
    work_end: str = Body("17:00:00"),
    auto_schedule: bool = Body(True),
    db: Session = Depends(get_db)
):
    """Quick setup: generate schedule and auto-schedule tasks in one call"""
    try:
        schedule_service = ScheduleGenerationService(db)
        
        # Generate weekly schedule
        schedule = schedule_service.generate_weekly_schedule(
            week_start_date=week_start,
            default_work_start=work_start,
            default_work_end=work_end,
            regenerate_if_exists=True
        )
        
        scheduled_tasks = []
        if auto_schedule:
            # Auto-schedule tasks
            scheduled_tasks = schedule_service.auto_schedule_tasks(
                schedule.id,
                max_tasks=100,
                allow_partial_scheduling=True
            )
        
        # Get summary
        summary = schedule_service.get_schedule_summary(schedule.id)
        
        return {
            "message": "Schedule created and tasks auto-scheduled",
            "schedule": schedule,
            "scheduled_task_count": len(scheduled_tasks),
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in quick schedule setup: {str(e)}"
        )