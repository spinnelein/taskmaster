"""
Schedule Generation Service - Create time pools and auto-schedule tasks
NO EMOJIS
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session

from ..data.models.schedule_model import ScheduleModel, TimePoolModel, TaskScheduleModel
from ..data.models.event_model import EventModel
from ..data.models.task_model import TaskModel, TaskStatus
from ..data.repositories.schedule_repo import ScheduleRepository, TimePoolRepository, TaskScheduleRepository
from ..data.repositories.event_repo import EventRepository
from .task_queue_service import TaskQueueService

logger = logging.getLogger(__name__)

class ScheduleGenerationService:
    """Service for generating schedules and time pools"""
    
    def __init__(self, db: Session):
        self.db = db
        self.schedule_repo = ScheduleRepository(db)
        self.time_pool_repo = TimePoolRepository(db)
        self.task_schedule_repo = TaskScheduleRepository(db)
        self.event_repo = EventRepository(db)
        self.task_queue_service = TaskQueueService(db)
    
    def generate_weekly_schedule(
        self, 
        week_start_date: Optional[date] = None,
        default_work_start: str = "09:00:00",
        default_work_end: str = "17:00:00",
        min_task_duration: int = 15,
        regenerate_if_exists: bool = False
    ) -> ScheduleModel:
        """Generate a complete weekly schedule with time pools"""
        
        if not week_start_date:
            # Get the start of current week (Monday)
            today = date.today()
            days_since_monday = today.weekday()
            week_start_date = today - timedelta(days=days_since_monday)
        
        week_end_date = week_start_date + timedelta(days=6)
        
        # Check if schedule already exists
        existing_schedule = self.schedule_repo.get_schedule_by_week(week_start_date)
        if existing_schedule and not regenerate_if_exists:
            logger.info(f"Schedule for week {week_start_date} already exists")
            return existing_schedule
        
        if existing_schedule and regenerate_if_exists:
            # Clean up existing schedule
            self._cleanup_schedule(existing_schedule.id)
            self.schedule_repo.delete(existing_schedule.id)
        
        # Create new schedule
        schedule_data = {
            "week_start_date": week_start_date,
            "week_end_date": week_end_date,
            "is_current": True,  # Set as current schedule
            "generated_at": datetime.now(),
            "default_work_start": default_work_start,
            "default_work_end": default_work_end,
            "min_task_duration_minutes": min_task_duration
        }
        
        # Unset any other current schedules
        self.db.query(ScheduleModel).filter(
            ScheduleModel.is_current == True
        ).update({"is_current": False})
        
        schedule = self.schedule_repo.create(schedule_data)
        
        # Generate time pools from events
        time_pools = self.generate_time_pools_from_events(schedule.id)
        
        logger.info(f"Generated schedule {schedule.id} with {len(time_pools)} time pools")
        
        return schedule
    
    def generate_time_pools_from_events(self, schedule_id: str) -> List[TimePoolModel]:
        """Generate time pools between blocking events"""
        schedule = self.schedule_repo.get(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        # Clear existing time pools
        self.db.query(TimePoolModel).filter(
            TimePoolModel.schedule_id == schedule_id
        ).delete()
        
        all_time_pools = []
        
        # Generate pools for each day of the week
        current_date = schedule.week_start_date
        while current_date <= schedule.week_end_date:
            # Skip weekends for now (can be made configurable)
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                daily_pools = self._generate_daily_time_pools(schedule, current_date)
                all_time_pools.extend(daily_pools)
            
            current_date += timedelta(days=1)
        
        self.db.commit()
        
        logger.info(f"Generated {len(all_time_pools)} time pools for schedule {schedule_id}")
        
        return all_time_pools
    
    def _generate_daily_time_pools(self, schedule: ScheduleModel, pool_date: date) -> List[TimePoolModel]:
        """Generate time pools for a single day between blocking events"""
        
        # Get all blocking events for this date
        blocking_events = self.event_repo.get_by_date(pool_date)
        blocking_events = [e for e in blocking_events if e.is_blocking]
        
        # Sort events by start time
        blocking_events.sort(key=lambda e: e.start_time)
        
        # Define work day boundaries
        work_start_time = datetime.strptime(schedule.default_work_start, "%H:%M:%S").time()
        work_end_time = datetime.strptime(schedule.default_work_end, "%H:%M:%S").time()
        
        work_start = datetime.combine(pool_date, work_start_time)
        work_end = datetime.combine(pool_date, work_end_time)
        
        time_pools = []
        current_time = work_start
        
        # Create time pools between events
        for event in blocking_events:
            # Skip events outside work hours
            if event.end_time <= work_start or event.start_time >= work_end:
                continue
            
            # Adjust event times to work hours
            event_start = max(event.start_time, work_start)
            event_end = min(event.end_time, work_end)
            
            # Create pool before event if there's enough time
            if current_time < event_start:
                pool_duration_minutes = int((event_start - current_time).total_seconds() / 60)
                
                if pool_duration_minutes >= schedule.min_task_duration_minutes:
                    pool = self._create_time_pool(
                        schedule.id,
                        pool_date,
                        current_time,
                        event_start,
                        pool_duration_minutes,
                        is_work_time=True,
                        is_flexible=True
                    )
                    time_pools.append(pool)
            
            # Move current time to after the event
            current_time = max(current_time, event_end)
        
        # Create final pool after all events if time remains
        if current_time < work_end:
            pool_duration_minutes = int((work_end - current_time).total_seconds() / 60)
            
            if pool_duration_minutes >= schedule.min_task_duration_minutes:
                pool = self._create_time_pool(
                    schedule.id,
                    pool_date,
                    current_time,
                    work_end,
                    pool_duration_minutes,
                    is_work_time=True,
                    is_flexible=True
                )
                time_pools.append(pool)
        
        # If no blocking events, create one large pool for the entire day
        if not blocking_events:
            full_day_minutes = int((work_end - work_start).total_seconds() / 60)
            
            if full_day_minutes >= schedule.min_task_duration_minutes:
                pool = self._create_time_pool(
                    schedule.id,
                    pool_date,
                    work_start,
                    work_end,
                    full_day_minutes,
                    is_work_time=True,
                    is_flexible=True
                )
                time_pools.append(pool)
        
        return time_pools
    
    def _create_time_pool(
        self,
        schedule_id: str,
        pool_date: date,
        start_time: datetime,
        end_time: datetime,
        total_minutes: int,
        is_work_time: bool = True,
        is_flexible: bool = True,
        weather_conditions: Optional[Dict[str, Any]] = None,
        context_tags: Optional[List[str]] = None
    ) -> TimePoolModel:
        """Create a time pool and save to database"""
        
        pool_data = {
            "schedule_id": schedule_id,
            "pool_date": pool_date,
            "start_time": start_time,
            "end_time": end_time,
            "total_minutes": total_minutes,
            "allocated_minutes": 0,
            "available_minutes": total_minutes,
            "weather_conditions": weather_conditions,
            "context_tags": context_tags,
            "is_work_time": is_work_time,
            "is_flexible": is_flexible
        }
        
        pool = self.time_pool_repo.create(pool_data)
        return pool
    
    def auto_schedule_tasks(
        self, 
        schedule_id: str,
        max_tasks: int = 50,
        prefer_due_date_order: bool = True,
        allow_partial_scheduling: bool = True
    ) -> List[TaskScheduleModel]:
        """Automatically schedule tasks into available time pools"""
        
        schedule = self.schedule_repo.get(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        # Get prioritized task queue
        task_queue = self.task_queue_service.get_task_queue(
            include_blocked=False,
            include_snoozed=False,
            limit=max_tasks
        )
        
        # Get available time pools
        available_pools = self.time_pool_repo.get_available_pools(
            schedule_id, 
            min_minutes=schedule.min_task_duration_minutes
        )
        
        if not available_pools:
            logger.warning(f"No available time pools for schedule {schedule_id}")
            return []
        
        scheduled_tasks = []
        
        for task_item in task_queue:
            if not task_item["can_be_scheduled"]:
                continue
            
            task = task_item["task"]
            remaining_duration = task.duration - (task.partial_completion_minutes or 0)
            
            if remaining_duration <= 0:
                continue  # Task is already completed
            
            # Find suitable time pools for this task
            suitable_pools = self._find_suitable_pools(
                task, 
                available_pools, 
                remaining_duration,
                prefer_due_date_order
            )
            
            if not suitable_pools:
                logger.debug(f"No suitable pools found for task {task.id}")
                continue
            
            # Schedule task into pools
            task_scheduled = False
            remaining_to_schedule = remaining_duration
            
            for pool in suitable_pools:
                if remaining_to_schedule <= 0:
                    break
                
                # Determine how much time to allocate in this pool
                allocation_minutes = min(
                    remaining_to_schedule,
                    pool.available_minutes,
                    240  # Max 4 hours per session
                )
                
                if allocation_minutes < schedule.min_task_duration_minutes:
                    continue
                
                # Create task schedule
                task_schedule = self._schedule_task_in_pool(
                    task, pool, allocation_minutes, schedule_id
                )
                
                if task_schedule:
                    scheduled_tasks.append(task_schedule)
                    remaining_to_schedule -= allocation_minutes
                    task_scheduled = True
                    
                    # Update pool availability
                    pool.allocated_minutes += allocation_minutes
                    pool.available_minutes -= allocation_minutes
                
                # If we've fully scheduled the task, move to next task
                if remaining_to_schedule <= 0:
                    break
                
                # If partial scheduling is not allowed, only schedule if we can fit the full task
                if not allow_partial_scheduling:
                    break
            
            if task_scheduled:
                logger.debug(f"Scheduled task {task.id} ({task.title})")
        
        self.db.commit()
        
        logger.info(f"Auto-scheduled {len(scheduled_tasks)} task sessions")
        
        return scheduled_tasks
    
    def _find_suitable_pools(
        self, 
        task: TaskModel, 
        available_pools: List[TimePoolModel],
        duration_needed: int,
        prefer_due_date_order: bool = True
    ) -> List[TimePoolModel]:
        """Find time pools suitable for scheduling a task"""
        
        suitable_pools = []
        
        for pool in available_pools:
            # Check if pool has minimum time available
            if pool.available_minutes < 15:  # Minimum 15 minutes
                continue
            
            # Check if pool is in a suitable time frame
            if task.due_date and prefer_due_date_order:
                # Prefer pools on or before due date
                if pool.pool_date > task.due_date:
                    # Only use pools after due date if no other options
                    continue
            
            # Check context conditions (placeholder for future implementation)
            # if task.condition_ids:
            #     if not self._check_context_conditions(task, pool):
            #         continue
            
            suitable_pools.append(pool)
        
        # Sort pools by preference
        if prefer_due_date_order:
            # Prefer earlier dates, then larger available chunks
            suitable_pools.sort(key=lambda p: (p.pool_date, -p.available_minutes))
        else:
            # Just sort by time
            suitable_pools.sort(key=lambda p: p.start_time)
        
        return suitable_pools
    
    def _schedule_task_in_pool(
        self, 
        task: TaskModel, 
        time_pool: TimePoolModel, 
        duration_minutes: int,
        schedule_id: str
    ) -> Optional[TaskScheduleModel]:
        """Schedule a specific task in a time pool"""
        
        try:
            # Calculate start and end times (use beginning of pool for now)
            scheduled_start = time_pool.start_time
            scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)
            
            # Make sure it fits in the pool
            if scheduled_end > time_pool.end_time:
                # Adjust to fit
                scheduled_end = time_pool.end_time
                duration_minutes = int((scheduled_end - scheduled_start).total_seconds() / 60)
            
            # Create task schedule
            task_schedule_data = {
                "task_id": task.id,
                "schedule_id": schedule_id,
                "time_pool_id": time_pool.id,
                "scheduled_start": scheduled_start,
                "scheduled_end": scheduled_end,
                "scheduled_duration_minutes": duration_minutes,
                "is_partial": duration_minutes < task.duration,
                "is_started": False,
                "is_completed": False,
                "minutes_worked": 0
            }
            
            task_schedule = self.task_schedule_repo.create(task_schedule_data)
            
            return task_schedule
            
        except Exception as e:
            logger.error(f"Error scheduling task {task.id} in pool {time_pool.id}: {e}")
            return None
    
    def _cleanup_schedule(self, schedule_id: str):
        """Clean up existing schedule data"""
        # Delete existing task schedules
        self.db.query(TaskScheduleModel).filter(
            TaskScheduleModel.schedule_id == schedule_id
        ).delete()
        
        # Delete existing time pools
        self.db.query(TimePoolModel).filter(
            TimePoolModel.schedule_id == schedule_id
        ).delete()
        
        self.db.commit()
    
    def regenerate_current_schedule(self) -> Optional[ScheduleModel]:
        """Regenerate the current week's schedule"""
        current_schedule = self.schedule_repo.get_current_schedule()
        
        if current_schedule:
            return self.generate_weekly_schedule(
                week_start_date=current_schedule.week_start_date,
                regenerate_if_exists=True
            )
        else:
            return self.generate_weekly_schedule()
    
    def get_schedule_summary(self, schedule_id: str) -> Dict[str, Any]:
        """Get a summary of a schedule's utilization"""
        
        schedule = self.schedule_repo.get(schedule_id)
        if not schedule:
            return {}
        
        # Get all time pools
        time_pools = self.time_pool_repo.get_by_schedule(schedule_id)
        
        # Get all scheduled tasks
        scheduled_tasks = self.task_schedule_repo.get_by_schedule(schedule_id)
        
        # Calculate statistics
        total_available_minutes = sum(pool.total_minutes for pool in time_pools)
        total_allocated_minutes = sum(pool.allocated_minutes for pool in time_pools)
        total_remaining_minutes = total_available_minutes - total_allocated_minutes
        
        utilization_rate = (total_allocated_minutes / total_available_minutes * 100) if total_available_minutes > 0 else 0
        
        completed_tasks = [t for t in scheduled_tasks if t.is_completed]
        pending_tasks = [t for t in scheduled_tasks if not t.is_completed]
        
        return {
            "schedule_id": schedule_id,
            "week_start": schedule.week_start_date,
            "week_end": schedule.week_end_date,
            "total_time_pools": len(time_pools),
            "total_available_minutes": total_available_minutes,
            "total_allocated_minutes": total_allocated_minutes,
            "total_remaining_minutes": total_remaining_minutes,
            "utilization_rate": round(utilization_rate, 2),
            "total_scheduled_tasks": len(scheduled_tasks),
            "completed_tasks": len(completed_tasks),
            "pending_tasks": len(pending_tasks),
            "average_task_duration": sum(t.scheduled_duration_minutes for t in scheduled_tasks) / len(scheduled_tasks) if scheduled_tasks else 0
        }