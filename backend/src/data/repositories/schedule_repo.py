"""
Schedule repository
NO EMOJIS
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, date, timedelta

from .base import BaseRepository
from ..models.schedule_model import ScheduleModel, TimePoolModel, TaskScheduleModel, ContextConditionModel
from ..models.task_model import TaskModel, TaskStatus
from ..models.event_model import EventModel

class ScheduleRepository(BaseRepository[ScheduleModel]):
    """Repository for schedule data operations"""
    
    def __init__(self, db: Session):
        super().__init__(ScheduleModel, db)
    
    def get_current_week(self) -> Optional[ScheduleModel]:
        """Get the current week's schedule"""
        return self.db.query(self.model).filter(
            self.model.is_current == True
        ).first()
    
    def get_by_week(self, week_start: date) -> Optional[ScheduleModel]:
        """Get schedule for a specific week"""
        return self.db.query(self.model).filter(
            self.model.week_start_date == week_start
        ).first()
    
    def get_with_pools(self, schedule_id: str) -> Optional[ScheduleModel]:
        """Get schedule with all time pools loaded"""
        return self.db.query(self.model).options(
            joinedload(self.model.time_pools),
            joinedload(self.model.scheduled_tasks)
        ).filter(
            self.model.id == schedule_id
        ).first()
    
    def create_time_pools_from_events(self, schedule_id: str) -> List[TimePoolModel]:
        """Create time pools between blocking events for a schedule"""
        schedule = self.get(schedule_id)
        if not schedule:
            return []
        
        # Clear existing pools
        self.db.query(TimePoolModel).filter(
            TimePoolModel.schedule_id == schedule_id
        ).delete()
        
        created_pools = []
        week_start = schedule.week_start_date
        week_end = schedule.week_end_date
        
        # For each day of the week
        current_date = week_start
        while current_date <= week_end:
            daily_pools = self._create_daily_time_pools(schedule_id, current_date)
            created_pools.extend(daily_pools)
            current_date += timedelta(days=1)
        
        self.db.commit()
        return created_pools
    
    def _create_daily_time_pools(self, schedule_id: str, pool_date: date) -> List[TimePoolModel]:
        """Create time pools for a single day"""
        schedule = self.get(schedule_id)
        pools = []
        
        # Get all blocking events for this date
        day_start = datetime.combine(pool_date, datetime.min.time())
        day_end = datetime.combine(pool_date, datetime.max.time())
        
        blocking_events = self.db.query(EventModel).filter(
            and_(
                EventModel.start_time >= day_start,
                EventModel.start_time <= day_end,
                EventModel.is_blocking == True
            )
        ).order_by(asc(EventModel.start_time)).all()
        
        # Define work day boundaries
        work_start = datetime.combine(pool_date, datetime.strptime(schedule.default_work_start, "%H:%M:%S").time())
        work_end = datetime.combine(pool_date, datetime.strptime(schedule.default_work_end, "%H:%M:%S").time())
        
        # Create pools between events
        current_time = work_start
        
        for event in blocking_events:
            # Create pool before event if there's time
            if current_time < event.start_time:
                pool_duration = (event.start_time - current_time).total_seconds() / 60
                
                if pool_duration >= schedule.min_task_duration_minutes:
                    pool = TimePoolModel(
                        schedule_id=schedule_id,
                        pool_date=pool_date,
                        start_time=current_time,
                        end_time=event.start_time,
                        total_minutes=int(pool_duration),
                        available_minutes=int(pool_duration),
                        is_work_time=True
                    )
                    self.db.add(pool)
                    pools.append(pool)
            
            # Move current time to after the event
            current_time = max(current_time, event.end_time)
        
        # Create final pool if time remains
        if current_time < work_end:
            pool_duration = (work_end - current_time).total_seconds() / 60
            
            if pool_duration >= schedule.min_task_duration_minutes:
                pool = TimePoolModel(
                    schedule_id=schedule_id,
                    pool_date=pool_date,
                    start_time=current_time,
                    end_time=work_end,
                    total_minutes=int(pool_duration),
                    available_minutes=int(pool_duration),
                    is_work_time=True
                )
                self.db.add(pool)
                pools.append(pool)
        
        return pools
    
    def get_unscheduled_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get prioritized list of unscheduled tasks"""
        # Get tasks that aren't scheduled and aren't completed/blocked
        unscheduled = self.db.query(TaskModel).filter(
            and_(
                TaskModel.status == TaskStatus.ACTIVE,
                ~TaskModel.id.in_(
                    self.db.query(TaskScheduleModel.task_id).filter(
                        TaskScheduleModel.is_completed == False
                    )
                )
            )
        ).all()
        
        task_queue = []
        current_time = datetime.utcnow()
        
        for task in unscheduled:
            # Calculate priority score
            priority_score = self._calculate_task_priority(task, current_time)
            
            # Check if task can be scheduled
            can_schedule, blocking_reasons = self._can_task_be_scheduled(task)
            
            task_queue.append({
                "task": task,
                "priority_score": priority_score,
                "is_overdue": self._is_task_overdue(task, current_time),
                "days_overdue": self._days_overdue(task, current_time),
                "can_be_scheduled": can_schedule,
                "blocking_reasons": blocking_reasons
            })
        
        # Sort by priority score (higher = more important)
        task_queue.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return task_queue[:limit]
    
    def _calculate_task_priority(self, task: TaskModel, current_time: datetime) -> float:
        """Calculate priority score for a task"""
        score = task.urgency  # Base urgency 1-10
        
        # Add overdue penalty
        if task.due_date:
            due_datetime = datetime.combine(task.due_date, task.due_time or datetime.min.time())
            if due_datetime < current_time:
                days_overdue = (current_time - due_datetime).days
                score += days_overdue * 2  # +2 points per day overdue
        
        # Non-recurring tasks get priority over recurring
        if not task.is_recurring:
            score += 3
        
        # Tasks with meal prep are high priority
        if task.meal_id:
            score += 5
        
        return score
    
    def _can_task_be_scheduled(self, task: TaskModel) -> Tuple[bool, List[str]]:
        """Check if a task can be scheduled"""
        blocking_reasons = []
        
        # Check dependencies
        if task.depends_on_task_ids:
            incomplete_deps = self.db.query(TaskModel).filter(
                and_(
                    TaskModel.id.in_(task.depends_on_task_ids),
                    TaskModel.status != TaskStatus.COMPLETED
                )
            ).count()
            
            if incomplete_deps > 0:
                blocking_reasons.append(f"{incomplete_deps} dependencies not completed")
        
        # Check if snoozed
        if task.is_snoozed and task.snoozed_until and task.snoozed_until > datetime.utcnow():
            blocking_reasons.append("Task is snoozed")
        
        # TODO: Check weather conditions
        # TODO: Check context conditions
        
        return len(blocking_reasons) == 0, blocking_reasons
    
    def _is_task_overdue(self, task: TaskModel, current_time: datetime) -> bool:
        """Check if task is overdue"""
        if not task.due_date:
            return False
        
        due_datetime = datetime.combine(task.due_date, task.due_time or datetime.min.time())
        return due_datetime < current_time
    
    def _days_overdue(self, task: TaskModel, current_time: datetime) -> int:
        """Calculate days overdue"""
        if not self._is_task_overdue(task, current_time):
            return 0
        
        due_datetime = datetime.combine(task.due_date, task.due_time or datetime.min.time())
        return (current_time - due_datetime).days
    
    def schedule_task(
        self, 
        task_id: str, 
        time_pool_id: str, 
        duration_minutes: Optional[int] = None,
        start_offset_minutes: int = 0
    ) -> Optional[TaskScheduleModel]:
        """Schedule a task into a time pool"""
        task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        time_pool = self.db.query(TimePoolModel).filter(TimePoolModel.id == time_pool_id).first()
        
        if not task or not time_pool:
            return None
        
        # Determine duration
        if duration_minutes is None:
            duration_minutes = task.remaining_minutes or task.duration
        
        # Check if pool has enough time
        if time_pool.available_minutes < duration_minutes:
            return None
        
        # Calculate start and end times
        scheduled_start = time_pool.start_time + timedelta(minutes=start_offset_minutes)
        scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)
        
        # Make sure it fits in the pool
        if scheduled_end > time_pool.end_time:
            return None
        
        # Create task schedule
        task_schedule = TaskScheduleModel(
            task_id=task_id,
            schedule_id=time_pool.schedule_id,
            time_pool_id=time_pool_id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            scheduled_duration_minutes=duration_minutes,
            is_partial=duration_minutes < task.duration
        )
        
        # Update time pool availability
        time_pool.allocated_minutes += duration_minutes
        time_pool.available_minutes -= duration_minutes
        
        # Update task remaining time if partial
        if task.remaining_minutes:
            task.remaining_minutes -= duration_minutes
        else:
            task.remaining_minutes = task.duration - duration_minutes
        
        self.db.add(task_schedule)
        self.db.commit()
        self.db.refresh(task_schedule)
        
        return task_schedule
    
    def auto_schedule_tasks(self, schedule_id: str, max_tasks: int = 50) -> List[TaskScheduleModel]:
        """Automatically schedule tasks into available time pools"""
        schedule = self.get_with_pools(schedule_id)
        if not schedule:
            return []
        
        scheduled_tasks = []
        task_queue = self.get_unscheduled_tasks(max_tasks)
        
        # Get available time pools sorted by date/time
        available_pools = [
            pool for pool in schedule.time_pools 
            if pool.available_minutes >= 15  # Minimum task time
        ]
        available_pools.sort(key=lambda p: p.start_time)
        
        for task_item in task_queue:
            if not task_item["can_be_scheduled"]:
                continue
            
            task = task_item["task"]
            task_duration = task.remaining_minutes or task.duration
            
            # Find suitable time pool
            for pool in available_pools:
                if pool.available_minutes >= min(task_duration, 15):  # Can fit at least 15 minutes
                    allocated_duration = min(task_duration, pool.available_minutes)
                    
                    scheduled_task = self.schedule_task(
                        task.id, 
                        pool.id, 
                        allocated_duration
                    )
                    
                    if scheduled_task:
                        scheduled_tasks.append(scheduled_task)
                        # If task is fully scheduled, move to next task
                        if allocated_duration >= task_duration:
                            break
        
        return scheduled_tasks

class TimePoolRepository(BaseRepository[TimePoolModel]):
    """Repository for time pool data operations"""
    
    def __init__(self, db: Session):
        super().__init__(TimePoolModel, db)
    
    def get_by_schedule(self, schedule_id: str) -> List[TimePoolModel]:
        """Get all time pools for a schedule"""
        return self.db.query(self.model).filter(
            self.model.schedule_id == schedule_id
        ).order_by(self.model.start_time).all()
    
    def get_available_pools(self, schedule_id: str, min_minutes: int = 15) -> List[TimePoolModel]:
        """Get time pools with available time"""
        return self.db.query(self.model).filter(
            and_(
                self.model.schedule_id == schedule_id,
                self.model.available_minutes >= min_minutes
            )
        ).order_by(self.model.start_time).all()

class TaskScheduleRepository(BaseRepository[TaskScheduleModel]):
    """Repository for task schedule data operations"""
    
    def __init__(self, db: Session):
        super().__init__(TaskScheduleModel, db)
    
    def get_by_task(self, task_id: str) -> List[TaskScheduleModel]:
        """Get all schedule entries for a task"""
        return self.db.query(self.model).filter(
            self.model.task_id == task_id
        ).order_by(self.model.scheduled_start).all()
    
    def get_current_task(self) -> Optional[TaskScheduleModel]:
        """Get the task that should be worked on now"""
        now = datetime.now()
        return self.db.query(self.model).filter(
            and_(
                self.model.scheduled_start <= now,
                self.model.scheduled_end > now,
                self.model.is_completed == False
            )
        ).first()