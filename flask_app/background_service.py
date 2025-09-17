"""
TaskMaster Background Service
Flask-integrated background processing for notifications, reminders, and scheduled tasks
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import requests
import os
import json
import uuid
from models import db, Event, Task, TimePool
from sqlalchemy import and_, or_
from recurring_service import recurring_service
from weather_service import get_flask_weather_service
from assignment_service import get_assignment_service

class TaskMasterBackgroundService:
    """
    Comprehensive background service for TaskMaster Flask application
    Handles event notifications, task reminders, and periodic maintenance
    """
    
    def __init__(self, app=None):
        self.app = app
        self.scheduler = None
        self.telegram_bot_token = None
        self.is_running = False
        self.telegram_chat_ids = set()
        self._setup_logging()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # Load chat IDs from file if exists
        self._load_telegram_chats()
        
        # Setup scheduler
        self.scheduler = BackgroundScheduler(timezone='America/Los_Angeles')
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        # Add shutdown handler
        import atexit
        atexit.register(self.stop)
    
    def _setup_logging(self):
        """Setup logging for background service"""
        self.logger = logging.getLogger('background_service')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _load_telegram_chats(self):
        """Load registered Telegram chat IDs"""
        chat_file = 'telegram_chats.txt'
        if os.path.exists(chat_file):
            try:
                with open(chat_file, 'r') as f:
                    for line in f:
                        chat_id = line.strip()
                        if chat_id:
                            self.telegram_chat_ids.add(int(chat_id))
                self.logger.info(f"Loaded {len(self.telegram_chat_ids)} Telegram chat IDs")
            except Exception as e:
                self.logger.error(f"Error loading Telegram chats: {e}")
    
    def _save_telegram_chat(self, chat_id: int):
        """Save new Telegram chat ID"""
        if chat_id not in self.telegram_chat_ids:
            self.telegram_chat_ids.add(chat_id)
            try:
                with open('telegram_chats.txt', 'a') as f:
                    f.write(f"{chat_id}\n")
                self.logger.info(f"Saved new Telegram chat ID: {chat_id}")
            except Exception as e:
                self.logger.error(f"Error saving Telegram chat: {e}")
    
    def start(self):
        """Start the background service"""
        if self.is_running:
            self.logger.warning("Background service already running")
            return
        
        try:
            # Schedule all background jobs
            self._schedule_jobs()
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            self.logger.info("TaskMaster Background Service started successfully")
            self.logger.info(f"Scheduled jobs: {len(self.scheduler.get_jobs())}")
            
            # Start Telegram webhook if token available
            if self.telegram_bot_token:
                self._start_telegram_webhook()
            
        except Exception as e:
            self.logger.error(f"Error starting background service: {e}")
            raise
    
    def stop(self):
        """Stop the background service"""
        if not self.is_running:
            return
        
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=True)
            self.is_running = False
            self.logger.info("TaskMaster Background Service stopped")
        except Exception as e:
            self.logger.error(f"Error stopping background service: {e}")
    
    def _schedule_jobs(self):
        """Schedule all background jobs"""
        
        # Event notifications - check every minute
        self.scheduler.add_job(
            func=self._process_event_notifications,
            trigger=IntervalTrigger(minutes=1),
            id='event_notifications',
            name='Process Event Notifications',
            max_instances=1,
            coalesce=True
        )
        
        # Task reminders - check every 2 minutes
        self.scheduler.add_job(
            func=self._process_task_reminders,
            trigger=IntervalTrigger(minutes=2),
            id='task_reminders',
            name='Process Task Reminders',
            max_instances=1,
            coalesce=True
        )
        
        # Daily schedule digest - 8 AM
        self.scheduler.add_job(
            func=self._send_daily_schedule,
            trigger=CronTrigger(hour=8, minute=0),
            id='daily_schedule',
            name='Send Daily Schedule Digest',
            max_instances=1
        )
        
        # Upcoming events reminder - 7 AM
        self.scheduler.add_job(
            func=self._send_upcoming_events,
            trigger=CronTrigger(hour=7, minute=0),
            id='upcoming_events',
            name='Send Upcoming Events Reminder',
            max_instances=1
        )
        
        # Daily task assignment - 6 AM (before other notifications)
        self.scheduler.add_job(
            func=self._regenerate_task_assignments,
            trigger=CronTrigger(hour=6, minute=0),
            id='regenerate_assignments',
            name='Regenerate Daily Task Assignments',
            max_instances=1
        )
        
        # Priority task notifications - every 4 hours during day
        self.scheduler.add_job(
            func=self._send_priority_task_reminder,
            trigger=CronTrigger(hour='8,12,16,20', minute=0),
            id='priority_tasks',
            name='Send Priority Task Reminders',
            max_instances=1
        )
        
        # Cleanup old notifications - daily at 2 AM
        self.scheduler.add_job(
            func=self._cleanup_old_data,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup',
            name='Cleanup Old Data',
            max_instances=1
        )
        
        # Health check - every 30 minutes
        self.scheduler.add_job(
            func=self._health_check,
            trigger=IntervalTrigger(minutes=30),
            id='health_check',
            name='Service Health Check',
            max_instances=1
        )
        
        # Time pool generation - daily at 3 AM
        self.scheduler.add_job(
            func=self._generate_time_pools,
            trigger=CronTrigger(hour=3, minute=0),
            id='generate_time_pools',
            name='Generate Time Pools',
            max_instances=1
        )
        
        # Weather forecast update - daily at 4 AM
        self.scheduler.add_job(
            func=self._update_weather_forecasts,
            trigger=CronTrigger(hour=4, minute=0),
            id='update_weather',
            name='Update Weather Forecasts',
            max_instances=1
        )
        
        # Initial time pool generation on startup (delayed 30 seconds)
        self.scheduler.add_job(
            func=self._generate_time_pools,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=30),
            id='startup_pool_generation',
            name='Startup Time Pool Generation',
            max_instances=1
        )
        
        # Initial weather update on startup (delayed 60 seconds)
        self.scheduler.add_job(
            func=self._update_weather_forecasts,
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
    
    def _process_event_notifications(self):
        """Process upcoming event notifications"""
        if not self.telegram_chat_ids:
            return
        
        with self.app.app_context():
            try:
                now = datetime.now()
                # Check for events starting in the next 5 minutes
                upcoming_events = db.session.query(Event).filter(
                    and_(
                        Event.start_time <= now + timedelta(minutes=5),
                        Event.start_time > now,
                        Event.notifications_enabled == True,
                        or_(Event.is_recurrence_master == True, Event.is_recurrence_master.is_(None))
                    )
                ).all()
                
                for event in upcoming_events:
                    self._send_event_notification(event)
                    
            except Exception as e:
                self.logger.error(f"Error processing event notifications: {e}")
    
    def _process_task_reminders(self):
        """Process task reminder notifications"""
        if not self.telegram_chat_ids:
            return
        
        with self.app.app_context():
            try:
                now = datetime.now()
                
                # Get high priority incomplete tasks
                high_priority_tasks = db.session.query(Task).filter(
                    and_(
                        Task.is_completed == False,
                        Task.urgency >= 8,
                        or_(Task.due_date.is_(None), Task.due_date >= now.date())
                    )
                ).order_by(Task.urgency.desc(), Task.created_at.asc()).limit(3).all()
                
                # Get overdue tasks
                overdue_tasks = db.session.query(Task).filter(
                    and_(
                        Task.is_completed == False,
                        Task.due_date < now.date()
                    )
                ).order_by(Task.due_date.asc()).limit(5).all()
                
                # Send notifications for priority and overdue tasks
                if high_priority_tasks or overdue_tasks:
                    self._send_task_reminder_batch(high_priority_tasks, overdue_tasks)
                    
            except Exception as e:
                self.logger.error(f"Error processing task reminders: {e}")
    
    def _send_event_notification(self, event: Event):
        """Send Telegram notification for event start"""
        if not self.telegram_bot_token:
            return
        
        try:
            start_time = event.start_time.strftime("%I:%M %p")
            duration = "Unknown"
            if event.end_time:
                delta = event.end_time - event.start_time
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                if hours > 0:
                    duration = f"{hours}h {minutes}m"
                else:
                    duration = f"{minutes}m"
            
            message = f"🎯 **Event Starting Soon**\n\n"
            message += f"**{event.title}**\n"
            message += f"⏰ Time: {start_time}\n"
            message += f"⏱️ Duration: {duration}\n"
            
            if event.location:
                message += f"📍 Location: {event.location}\n"
            
            if event.description:
                message += f"📝 Description: {event.description}\n"
            
            if event.is_blocking:
                message += f"🚫 Blocking Event\n"
            
            self._send_telegram_message(message)
            
            # Update event status to in_progress
            event.status = 'in_progress'
            db.session.commit()
            
            self.logger.info(f"Sent event notification: {event.title}")
            
        except Exception as e:
            self.logger.error(f"Error sending event notification: {e}")
    
    def _send_task_reminder_batch(self, high_priority_tasks: List[Task], overdue_tasks: List[Task]):
        """Send batch task reminder notification"""
        if not self.telegram_bot_token:
            return
        
        try:
            message = "📋 **Task Reminder**\n\n"
            
            if overdue_tasks:
                message += "🔴 **Overdue Tasks:**\n"
                for task in overdue_tasks:
                    days_overdue = (datetime.now().date() - task.due_date).days
                    message += f"• {task.title} ({days_overdue} days overdue)\n"
                message += "\n"
            
            if high_priority_tasks:
                message += "⚡ **High Priority Tasks:**\n"
                for task in high_priority_tasks:
                    urgency_emoji = "🔥" if task.urgency >= 9 else "⚡"
                    message += f"{urgency_emoji} {task.title} (Urgency: {task.urgency})\n"
                message += "\n"
            
            message += "💡 Stay focused and tackle these important tasks!"
            
            self._send_telegram_message(message)
            self.logger.info(f"Sent task reminder batch: {len(high_priority_tasks + overdue_tasks)} tasks")
            
        except Exception as e:
            self.logger.error(f"Error sending task reminder batch: {e}")
    
    def _send_daily_schedule(self):
        """Send daily schedule digest"""
        if not self.telegram_chat_ids:
            return
        
        with self.app.app_context():
            try:
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                
                # Get today's events
                todays_events = db.session.query(Event).filter(
                    and_(
                        Event.start_time >= datetime.combine(today, datetime.min.time()),
                        Event.start_time < datetime.combine(tomorrow, datetime.min.time()),
                        or_(Event.is_recurrence_master == True, Event.is_recurrence_master.is_(None))
                    )
                ).order_by(Event.start_time).all()
                
                # Get today's tasks due
                todays_tasks = db.session.query(Task).filter(
                    and_(
                        Task.due_date == today,
                        Task.is_completed == False
                    )
                ).order_by(Task.urgency.desc()).all()
                
                if not todays_events and not todays_tasks:
                    message = f"🌅 **Good Morning!**\n\nYou have a light day ahead - no scheduled events or due tasks. Perfect time to work on longer-term projects!"
                else:
                    message = f"🌅 **Good Morning! Here's your day:**\n\n"
                    
                    if todays_events:
                        message += "📅 **Today's Events:**\n"
                        for event in todays_events:
                            time_str = event.start_time.strftime("%I:%M %p")
                            message += f"• {time_str} - {event.title}\n"
                        message += "\n"
                    
                    if todays_tasks:
                        message += "✅ **Tasks Due Today:**\n"
                        for task in todays_tasks:
                            urgency_emoji = "🔥" if task.urgency >= 8 else "⚡" if task.urgency >= 5 else "📝"
                            message += f"{urgency_emoji} {task.title}\n"
                        message += "\n"
                    
                    message += "💪 Have a productive day!"
                
                self._send_telegram_message(message)
                self.logger.info("Sent daily schedule digest")
                
            except Exception as e:
                self.logger.error(f"Error sending daily schedule: {e}")
    
    def _send_upcoming_events(self):
        """Send upcoming events for the day"""
        if not self.telegram_chat_ids:
            return
        
        with self.app.app_context():
            try:
                now = datetime.now()
                end_of_day = datetime.combine(now.date(), datetime.max.time())
                
                upcoming_events = db.session.query(Event).filter(
                    and_(
                        Event.start_time > now,
                        Event.start_time <= end_of_day,
                        or_(Event.is_recurrence_master == True, Event.is_recurrence_master.is_(None))
                    )
                ).order_by(Event.start_time).all()
                
                if upcoming_events:
                    message = "⏰ **Upcoming Events Today:**\n\n"
                    for event in upcoming_events:
                        time_str = event.start_time.strftime("%I:%M %p")
                        time_until = event.start_time - now
                        hours_until = time_until.seconds // 3600
                        minutes_until = (time_until.seconds % 3600) // 60
                        
                        if hours_until > 0:
                            time_desc = f"in {hours_until}h {minutes_until}m"
                        else:
                            time_desc = f"in {minutes_until}m"
                        
                        message += f"• {time_str} - {event.title} ({time_desc})\n"
                    
                    self._send_telegram_message(message)
                    self.logger.info(f"Sent upcoming events notification: {len(upcoming_events)} events")
                
            except Exception as e:
                self.logger.error(f"Error sending upcoming events: {e}")
    
    def _send_priority_task_reminder(self):
        """Send priority task reminder"""
        if not self.telegram_chat_ids:
            return
        
        with self.app.app_context():
            try:
                # Get top 3 priority incomplete tasks
                priority_tasks = db.session.query(Task).filter(
                    Task.is_completed == False
                ).order_by(Task.urgency.desc(), Task.created_at.asc()).limit(3).all()
                
                if priority_tasks:
                    message = "🎯 **Focus Time! Top Priority Tasks:**\n\n"
                    for i, task in enumerate(priority_tasks, 1):
                        urgency_emoji = "🔥" if task.urgency >= 8 else "⚡" if task.urgency >= 5 else "📝"
                        duration_text = f" ({task.duration}min)" if task.duration else ""
                        message += f"{i}. {urgency_emoji} {task.title}{duration_text}\n"
                    
                    message += "\n💡 Pick one and make progress!"
                    
                    self._send_telegram_message(message)
                    self.logger.info(f"Sent priority task reminder: {len(priority_tasks)} tasks")
                
            except Exception as e:
                self.logger.error(f"Error sending priority task reminder: {e}")
    
    def _update_weather_forecasts(self):
        """Update weather forecasts from API"""
        with self.app.app_context():
            try:
                weather_service = get_flask_weather_service()
                
                # Update forecast data from API (7 days ahead)
                saved_count = asyncio.run(weather_service.update_forecast_from_api(days=7))
                
                # Clean up old forecasts (keep 30 days)
                deleted_count = weather_service.delete_old_forecasts(days_to_keep=30)
                
                self.logger.info(f"Weather update complete: {saved_count} forecasts updated, {deleted_count} old forecasts deleted")
                
            except Exception as e:
                self.logger.error(f"Error updating weather forecasts: {e}")
    
    def _cleanup_old_data(self):
        """Cleanup old data and logs"""
        with self.app.app_context():
            try:
                # This is a placeholder for future cleanup operations
                # Could clean old logs, completed tasks, etc.
                self.logger.info("Performed daily cleanup")
                
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
    
    def _health_check(self):
        """Perform health check"""
        try:
            # Check database connection
            with self.app.app_context():
                db.session.execute('SELECT 1')
            
            # Check scheduler health
            running_jobs = len(self.scheduler.get_jobs())
            
            self.logger.info(f"Health check passed - {running_jobs} scheduled jobs running")
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
    
    def _send_telegram_message(self, message: str):
        """Send message to all registered Telegram chats"""
        if not self.telegram_bot_token or not self.telegram_chat_ids:
            return
        
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        
        for chat_id in self.telegram_chat_ids.copy():  # Copy to avoid modification during iteration
            try:
                data = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, json=data, timeout=10)
                
                if response.status_code == 200:
                    self.logger.debug(f"Message sent to chat {chat_id}")
                else:
                    self.logger.warning(f"Failed to send message to chat {chat_id}: {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Error sending message to chat {chat_id}: {e}")
    
    def _start_telegram_webhook(self):
        """Start simple Telegram webhook for user registration"""
        # This is a simplified webhook - in production you'd want proper webhook handling
        self.logger.info("Telegram integration ready - users can register with /start command")
    
    def _generate_time_pools(self):
        """Generate time pools based on scheduled events"""
        with self.app.app_context():
            try:
                # Define work hours (6 AM to 11 PM for broader coverage)
                work_start_hour = 6
                work_end_hour = 19
                min_pool_duration = 30  # Minimum 30 minutes
                
                # Find date range based on actual events (limited to 30 days ahead)
                earliest_event = db.session.query(Event.start_time).order_by(Event.start_time.asc()).first()
                latest_event = db.session.query(Event.start_time).order_by(Event.start_time.desc()).first()
                
                if not earliest_event or not latest_event:
                    self.logger.info("No events found - creating pools for next 30 days")
                    start_date = datetime.now().date()
                    end_date = start_date + timedelta(days=30)
                else:
                    # Include actual event dates but limit future generation to 30 days
                    start_date = min(earliest_event[0].date(), datetime.now().date())
                    max_future_date = datetime.now().date() + timedelta(days=30)
                    end_date = min(max(latest_event[0].date(), datetime.now().date()), max_future_date)
                
                self.logger.info(f"Generating time pools from {start_date} to {end_date}")
                
                # Clean up old pools (older than start_date)
                old_pools = TimePool.query.filter(TimePool.pool_date < start_date).all()
                for pool in old_pools:
                    db.session.delete(pool)
                
                pools_created = 0
                pools_updated = 0
                
                # Process each day in the range
                current_date = start_date
                while current_date <= end_date:
                    day_pools_created, day_pools_updated = self._generate_pools_for_date(
                        current_date, work_start_hour, work_end_hour, min_pool_duration
                    )
                    pools_created += day_pools_created
                    pools_updated += day_pools_updated
                    current_date += timedelta(days=1)
                
                db.session.commit()
                self.logger.info(f"Time pool generation complete: {pools_created} created, {pools_updated} updated")
                
                # Regenerate task assignments after daily pool generation
                self._regenerate_task_assignments(context="daily_generation")
                
            except Exception as e:
                self.logger.error(f"Error generating time pools: {e}")
                db.session.rollback()
    
    def _generate_pools_for_date(self, target_date, work_start_hour, work_end_hour, min_pool_duration):
        """Generate time pools for a specific date"""
        pools_created = 0
        pools_updated = 0
        
        # Get only master recurring events for expansion
        master_recurring_events = Event.query.filter(
            Event.is_recurrence_master == True
        ).all()
        
        # Expand recurring events for this specific date
        expanded_events = recurring_service.expand_events_for_period(master_recurring_events, target_date, target_date)
        
        self.logger.info(f"Expanded {len(expanded_events)} events for {target_date}")
        
        # Filter to only blocking events and convert to event-like objects
        blocking_events = []
        for event_dict in expanded_events:
            if event_dict.get('is_blocking', False):
                # Create a simple object with the needed attributes
                class EventInstance:
                    def __init__(self, event_dict):
                        self.start_time = datetime.fromisoformat(event_dict['start'])
                        self.end_time = datetime.fromisoformat(event_dict['end'])
                        self.title = event_dict['title']
                        self.is_blocking = event_dict['is_blocking']
                        self.buffer_before_minutes = 0
                        self.buffer_after_minutes = 0
                
                blocking_events.append(EventInstance(event_dict))
                self.logger.info(f"Added blocking event: {event_dict['title']} at {event_dict['start']}")
        
        # Also get any non-recurring events for this date
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date, datetime.max.time())
        
        non_recurring_events = db.session.query(Event).filter(
            and_(
                Event.start_time >= day_start,
                Event.start_time <= day_end,
                Event.is_blocking == True,
                or_(Event.is_recurring.is_(None), Event.is_recurring == False)
            )
        ).all()
        
        blocking_events.extend(non_recurring_events)
        
        self.logger.info(f"Found {len(blocking_events)} total blocking events for {target_date}")
        
        # Delete existing pools for this date to regenerate
        existing_pools = TimePool.query.filter(TimePool.pool_date == target_date).all()
        for pool in existing_pools:
            db.session.delete(pool)
        
        # If no events, create one large pool for the work day
        if not blocking_events:
            work_day_start = datetime.combine(target_date, datetime.min.time().replace(hour=work_start_hour))
            work_day_end = datetime.combine(target_date, datetime.min.time().replace(hour=work_end_hour))
            work_duration = (work_day_end - work_day_start).total_seconds() / 60
            
            if work_duration >= min_pool_duration:
                pool = self._create_time_pool(target_date, work_day_start, work_day_end, work_duration)
                if pool:
                    pools_created += 1
            return pools_created, pools_updated
        
        # Process events to find gaps
        work_day_start = datetime.combine(target_date, datetime.min.time().replace(hour=work_start_hour))
        work_day_end = datetime.combine(target_date, datetime.min.time().replace(hour=work_end_hour))
        
        # Create list of time slots occupied by events
        occupied_slots = []
        for event in blocking_events:
            start_time = max(event.start_time, work_day_start)  # Don't go before work hours
            end_time = min(event.end_time or event.start_time + timedelta(hours=1), work_day_end)  # Don't go past work hours
            
            # Add buffer time if specified
            buffer_before = getattr(event, 'buffer_before_minutes', 0) or 0
            buffer_after = getattr(event, 'buffer_after_minutes', 0) or 0
            
            buffer_start = start_time - timedelta(minutes=buffer_before)
            buffer_end = end_time + timedelta(minutes=buffer_after)
            
            # Keep within work hours
            buffer_start = max(buffer_start, work_day_start)
            buffer_end = min(buffer_end, work_day_end)
            
            occupied_slots.append((buffer_start, buffer_end))
        
        # Merge overlapping occupied slots
        occupied_slots.sort()
        merged_slots = []
        for start, end in occupied_slots:
            if merged_slots and start <= merged_slots[-1][1]:
                # Overlapping - extend the last slot
                merged_slots[-1] = (merged_slots[-1][0], max(merged_slots[-1][1], end))
            else:
                merged_slots.append((start, end))
        
        # Find gaps between occupied slots and create pools
        current_time = work_day_start
        
        for occupied_start, occupied_end in merged_slots:
            # Create pool before this occupied slot
            if occupied_start > current_time:
                gap_duration = (occupied_start - current_time).total_seconds() / 60
                if gap_duration >= min_pool_duration:
                    pool = self._create_time_pool(target_date, current_time, occupied_start, gap_duration)
                    if pool:
                        pools_created += 1
                        self.logger.debug(f"Created pool: {current_time.strftime('%H:%M')} - {occupied_start.strftime('%H:%M')} ({gap_duration:.0f}min)")
            
            # Move current time to end of this occupied slot
            current_time = occupied_end
        
        # Create final pool if there's time left after the last event
        if current_time < work_day_end:
            final_duration = (work_day_end - current_time).total_seconds() / 60
            if final_duration >= min_pool_duration:
                pool = self._create_time_pool(target_date, current_time, work_day_end, final_duration)
                if pool:
                    pools_created += 1
                    self.logger.debug(f"Created final pool: {current_time.strftime('%H:%M')} - {work_day_end.strftime('%H:%M')} ({final_duration:.0f}min)")
        
        return pools_created, pools_updated
    
    def _create_time_pool(self, pool_date, start_time, end_time, duration_minutes):
        """Create a time pool record"""
        try:
            from models import WeatherForecast
            
            # Determine context tags based on time period (not just start hour)
            start_hour = start_time.hour
            end_hour = end_time.hour
            duration_hours = (end_time - start_time).total_seconds() / 3600
            context_tags = []
            
            # For pools longer than 4 hours, determine dominant work period
            if duration_hours > 4:
                # Long pool - determine if it's primarily work time
                work_hours_covered = 0
                for h in range(start_hour, end_hour + 1):
                    if 8 <= h <= 20:  # Business hours 8 AM - 8 PM
                        work_hours_covered += 1
                
                if work_hours_covered >= (end_hour - start_hour) * 0.6:  # 60% work time
                    context_tags = ['work_day', 'work_time', 'mixed_periods']
                    is_work_time = True
                else:
                    context_tags = ['mixed_periods', 'personal_time']
                    is_work_time = False
            else:
                # Short pool - use start hour logic
                if 8 <= start_hour < 12:
                    context_tags = ['morning', 'work_time', 'focus_time']
                    is_work_time = True
                elif 12 <= start_hour < 14:
                    context_tags = ['lunch_time', 'break_time']
                    is_work_time = False
                elif 14 <= start_hour < 18:
                    context_tags = ['afternoon', 'work_time', 'meetings']
                    is_work_time = True
                elif 18 <= start_hour < 20:
                    context_tags = ['evening', 'work_time', 'admin_time']
                    is_work_time = True
                elif 20 <= start_hour < 22:
                    context_tags = ['evening', 'personal_time', 'flexible']
                    is_work_time = False
                else:
                    context_tags = ['off_hours', 'personal_time']
                    is_work_time = False
            
            # Get weather forecast for this date
            weather_forecast = WeatherForecast.get_by_date(pool_date)
            weather_forecast_id = weather_forecast.id if weather_forecast else None
            
            # Add weather-based context tags
            if weather_forecast:
                if weather_forecast.is_suitable_for_outdoor_work():
                    context_tags.append('good_weather')
                    context_tags.append('outdoor_suitable')
                else:
                    context_tags.append('indoor_preferred')
                
                comfort_level = weather_forecast.get_comfort_level()
                context_tags.append(f'weather_{comfort_level}')
                
                if weather_forecast.precipitation_probability and weather_forecast.precipitation_probability > 50:
                    context_tags.append('rain_likely')
            
            # Create the time pool
            pool = TimePool(
                id=str(uuid.uuid4()),
                pool_date=pool_date,
                start_time=start_time,
                end_time=end_time,
                total_minutes=int(duration_minutes),
                allocated_minutes=0,
                available_minutes=int(duration_minutes),
                is_work_time=is_work_time,
                is_flexible=True,
                context_tags=json.dumps(context_tags),
                weather_forecast_id=weather_forecast_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(pool)
            return pool
            
        except Exception as e:
            self.logger.error(f"Error creating time pool: {e}")
            return None
    
    def regenerate_time_pools(self):
        """Public method to trigger time pool regeneration"""
        if self.scheduler and self.is_running:
            # Schedule immediate regeneration
            self.scheduler.add_job(
                func=self._generate_time_pools,
                trigger='date',
                run_date=datetime.now() + timedelta(seconds=5),
                id=f'manual_pool_regen_{int(time.time())}',
                name='Manual Time Pool Regeneration',
                max_instances=1
            )
            self.logger.info("Scheduled immediate time pool regeneration")
        else:
            self.logger.warning("Cannot regenerate pools - scheduler not running")
    
    def regenerate_all_time_pools(self, max_days_ahead: int = 30):
        """
        Regenerate time pools for all dates (up to max_days_ahead).
        This method can be called directly without the scheduler.
        """
        with self.app.app_context():
            try:
                # Delete all existing pools to start fresh
                all_pools = TimePool.query.all()
                pool_count = len(all_pools)
                for pool in all_pools:
                    db.session.delete(pool)
                db.session.commit()
                self.logger.info(f"Deleted {pool_count} existing time pools")
                
                # Find date range based on actual events (limited to max_days_ahead)
                earliest_event = db.session.query(Event.start_time).order_by(Event.start_time.asc()).first()
                latest_event = db.session.query(Event.start_time).order_by(Event.start_time.desc()).first()
                
                if not earliest_event or not latest_event:
                    self.logger.info(f"No events found - creating pools for next {max_days_ahead} days")
                    start_date = datetime.now().date()
                    end_date = start_date + timedelta(days=max_days_ahead)
                else:
                    # Include actual event dates but limit future generation
                    start_date = min(earliest_event[0].date(), datetime.now().date())
                    max_future_date = datetime.now().date() + timedelta(days=max_days_ahead)
                    end_date = min(latest_event[0].date(), max_future_date)
                
                self.logger.info(f"Regenerating time pools from {start_date} to {end_date}")
                
                pools_created = 0
                pools_updated = 0
                
                # Process each day in the range
                current_date = start_date
                while current_date <= end_date:
                    day_pools_created, day_pools_updated = self._generate_pools_for_date(
                        current_date, 6, 23, 30
                    )
                    pools_created += day_pools_created
                    pools_updated += day_pools_updated
                    current_date += timedelta(days=1)
                
                db.session.commit()
                self.logger.info(f"Full regeneration complete: {pools_created} pools created, {pools_updated} updated")
                
                # Regenerate task assignments after pool regeneration
                self._regenerate_task_assignments(context="full_regeneration")
                
                return pools_created, pools_updated
                
            except Exception as e:
                self.logger.error(f"Error during full regeneration: {e}")
                db.session.rollback()
                raise
    
    def update_time_pools_for_range(self, start_date: date, end_date: date):
        """
        Update time pools for a specific date range.
        More efficient than full regeneration for smaller ranges.
        """
        with self.app.app_context():
            try:
                self.logger.info(f"Updating time pools from {start_date} to {end_date}")
                
                # Delete existing pools for this date range
                existing_pools = TimePool.query.filter(
                    TimePool.pool_date >= start_date,
                    TimePool.pool_date <= end_date
                ).all()
                
                pool_count = len(existing_pools)
                for pool in existing_pools:
                    db.session.delete(pool)
                
                self.logger.info(f"Deleted {pool_count} existing pools in date range")
                
                pools_created = 0
                pools_updated = 0
                
                # Process each day in the range
                current_date = start_date
                while current_date <= end_date:
                    day_pools_created, day_pools_updated = self._generate_pools_for_date(
                        current_date, 6, 23, 30
                    )
                    pools_created += day_pools_created
                    pools_updated += day_pools_updated
                    current_date += timedelta(days=1)
                
                db.session.commit()
                self.logger.info(f"Range update complete: {pools_created} pools created, {pools_updated} updated")
                
                # Regenerate task assignments after range update
                self._regenerate_task_assignments(context="range_update")
                
                return pools_created, pools_updated
                
            except Exception as e:
                self.logger.error(f"Error updating pools for range: {e}")
                db.session.rollback()
                raise
    
    def _regenerate_task_assignments(self, context: str = "scheduled"):
        """
        Regenerate task assignments after time pool changes.
        Uses the existing bulk assignment system to reassign all tasks.
        """
        try:
            with self.app.app_context():
                assignment_service = get_assignment_service()
                
                result = assignment_service.bulk_assign_tasks_to_pools(
                    clear_existing=True,
                    max_days_ahead=7,
                    assigned_by=f'auto_{context}'
                )
                
                if result['success']:
                    self.logger.info(f"Task assignment regeneration ({context}): {result['message']}")
                    return result
                else:
                    self.logger.error(f"Task assignment regeneration failed ({context}): {result['message']}")
                    return result
                    
        except Exception as e:
            self.logger.error(f"Error regenerating task assignments ({context}): {e}")
            return {
                'success': False,
                'message': f"Assignment regeneration failed: {str(e)}",
                'assignments_made': [],
                'tasks_processed': 0,
                'pools_used': 0,
                'unassigned_tasks': []
            }
    
    def register_telegram_chat(self, chat_id: int):
        """Register a new Telegram chat ID"""
        self._save_telegram_chat(chat_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        status = {
            'running': self.is_running,
            'scheduler_running': self.scheduler.running if self.scheduler else False,
            'scheduled_jobs': len(self.scheduler.get_jobs()) if self.scheduler else 0,
            'telegram_enabled': bool(self.telegram_bot_token),
            'registered_chats': len(self.telegram_chat_ids),
            'uptime': time.time() - getattr(self, '_start_time', time.time())
        }
        
        # Add time pool statistics if app context available
        try:
            if self.app:
                with self.app.app_context():
                    today = datetime.now().date()
                    total_pools = TimePool.query.count()
                    future_pools = TimePool.query.filter(TimePool.pool_date >= today).count()
                    available_pools = TimePool.query.filter(
                        and_(TimePool.pool_date >= today, TimePool.available_minutes > 0)
                    ).count()
                    
                    status.update({
                        'total_time_pools': total_pools,
                        'future_pools': future_pools,
                        'available_pools': available_pools
                    })
        except Exception as e:
            self.logger.debug(f"Could not get pool statistics: {e}")
        
        return status

# Global service instance
background_service = TaskMasterBackgroundService()