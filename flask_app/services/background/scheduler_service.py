"""
TaskMaster Scheduler Service
Manages APScheduler jobs and background task scheduling
"""

import logging
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


class SchedulerService:
    """Service for managing background job scheduling"""
    
    def __init__(self, app=None):
        self.app = app
        self.scheduler = None
        self.is_running = False
        self._start_time = time.time()
        self.logger = logging.getLogger('scheduler_service')
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Setup scheduler
        self.scheduler = BackgroundScheduler(timezone='America/Los_Angeles')
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        # Add shutdown handler
        import atexit
        atexit.register(self.stop)
    
    def start(self, job_functions):
        """Start the scheduler with provided job functions"""
        if self.is_running:
            self.logger.warning("Scheduler already running")
            return
        
        try:
            # Schedule all background jobs
            self._schedule_jobs(job_functions)
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            self._start_time = time.time()
            
            self.logger.info("TaskMaster Scheduler started successfully")
            self.logger.info(f"Scheduled jobs: {len(self.scheduler.get_jobs())}")
            
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=True)
            self.is_running = False
            self.logger.info("TaskMaster Scheduler stopped")
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
    
    def _schedule_jobs(self, job_functions):
        """Schedule all background jobs"""
        
        # Event notifications - check every minute
        self.scheduler.add_job(
            func=job_functions['process_event_notifications'],
            trigger=IntervalTrigger(minutes=1),
            id='event_notifications',
            name='Process Event Notifications',
            max_instances=1,
            coalesce=True
        )
        
        # Task reminders - check every 2 minutes
        self.scheduler.add_job(
            func=job_functions['process_task_reminders'],
            trigger=IntervalTrigger(minutes=2),
            id='task_reminders',
            name='Process Task Reminders',
            max_instances=1,
            coalesce=True
        )
        
        # Daily schedule digest - 8 AM
        self.scheduler.add_job(
            func=job_functions['send_daily_schedule'],
            trigger=CronTrigger(hour=8, minute=0),
            id='daily_schedule',
            name='Send Daily Schedule Digest',
            max_instances=1
        )
        
        # Upcoming events reminder - 7 AM
        self.scheduler.add_job(
            func=job_functions['send_upcoming_events'],
            trigger=CronTrigger(hour=7, minute=0),
            id='upcoming_events',
            name='Send Upcoming Events Reminder',
            max_instances=1
        )
        
        # Daily task assignment - 6 AM (before other notifications)
        self.scheduler.add_job(
            func=job_functions['regenerate_task_assignments'],
            trigger=CronTrigger(hour=6, minute=0),
            id='regenerate_assignments',
            name='Regenerate Daily Task Assignments',
            max_instances=1
        )
        
        # Priority task notifications - every 4 hours during day
        self.scheduler.add_job(
            func=job_functions['send_priority_task_reminder'],
            trigger=CronTrigger(hour='8,12,16,20', minute=0),
            id='priority_tasks',
            name='Send Priority Task Reminders',
            max_instances=1
        )
        
        # Cleanup old notifications - daily at 2 AM
        self.scheduler.add_job(
            func=job_functions['cleanup_old_data'],
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup',
            name='Cleanup Old Data',
            max_instances=1
        )
        
        # Health check - every 30 minutes
        self.scheduler.add_job(
            func=job_functions['health_check'],
            trigger=IntervalTrigger(minutes=30),
            id='health_check',
            name='Service Health Check',
            max_instances=1
        )
        
        # Time pool generation - daily at 3 AM
        self.scheduler.add_job(
            func=job_functions['generate_time_pools'],
            trigger=CronTrigger(hour=3, minute=0),
            id='generate_time_pools',
            name='Generate Time Pools',
            max_instances=1
        )
        
        # Weather forecast update - daily at 4 AM
        self.scheduler.add_job(
            func=job_functions['update_weather_forecasts'],
            trigger=CronTrigger(hour=4, minute=0),
            id='update_weather',
            name='Update Weather Forecasts',
            max_instances=1
        )
        
        # Initial time pool generation on startup (delayed 30 seconds)
        self.scheduler.add_job(
            func=job_functions['generate_time_pools'],
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=30),
            id='startup_pool_generation',
            name='Startup Time Pool Generation',
            max_instances=1
        )
        
        # Initial weather update on startup (delayed 60 seconds)
        self.scheduler.add_job(
            func=job_functions['update_weather_forecasts'],
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=60),
            id='startup_weather_update',
            name='Startup Weather Update',
            max_instances=1
        )
    
    def _job_listener(self, event):
        """Listen to job execution events"""
        if event.exception:
            self.logger.error(f"Job {event.job_id} crashed: {event.exception}")
        else:
            self.logger.debug(f"Job {event.job_id} executed successfully")
    
    def add_job(self, func, trigger, job_id, name, **kwargs):
        """Add a new job to the scheduler"""
        if self.scheduler:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name,
                **kwargs
            )
            self.logger.info(f"Added job: {name}")
    
    def remove_job(self, job_id):
        """Remove a job from the scheduler"""
        if self.scheduler:
            try:
                self.scheduler.remove_job(job_id)
                self.logger.info(f"Removed job: {job_id}")
            except Exception as e:
                self.logger.error(f"Error removing job {job_id}: {e}")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        if self.scheduler:
            return self.scheduler.get_jobs()
        return []
    
    def get_status(self):
        """Get scheduler status"""
        return {
            'running': self.is_running,
            'scheduler_running': self.scheduler.running if self.scheduler else False,
            'scheduled_jobs': len(self.scheduler.get_jobs()) if self.scheduler else 0,
            'uptime': time.time() - self._start_time
        }