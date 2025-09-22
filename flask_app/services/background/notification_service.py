"""
TaskMaster Notification Service
Handles Telegram notifications for events and tasks
"""

import logging
import requests
import os
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import and_, or_
from flask import current_app
from models import db, Event, Task


class NotificationService:
    """Service for handling all notification functionality"""
    
    def __init__(self, app=None):
        self.app = app
        self.telegram_bot_token = None
        self.telegram_chat_ids = set()
        self.logger = logging.getLogger('notification_service')
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self._load_telegram_chats()
    
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
    
    def register_telegram_chat(self, chat_id: int):
        """Register a new Telegram chat ID"""
        self._save_telegram_chat(chat_id)
    
    def process_event_notifications(self):
        """Process upcoming event notifications"""
        if not self.telegram_chat_ids:
            return
        
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
    
    def process_task_reminders(self):
        """Process task reminder notifications"""
        if not self.telegram_chat_ids:
            return
        
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
    
    def send_daily_schedule(self):
        """Send daily schedule digest"""
        if not self.telegram_chat_ids:
            return
        
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
                message = f"Good Morning!\n\nYou have a light day ahead - no scheduled events or due tasks. Perfect time to work on longer-term projects!"
            else:
                message = f"Good Morning! Here's your day:\n\n"
                
                if todays_events:
                    message += "Today's Events:\n"
                    for event in todays_events:
                        time_str = event.start_time.strftime("%I:%M %p")
                        message += f"• {time_str} - {event.title}\n"
                    message += "\n"
                
                if todays_tasks:
                    message += "Tasks Due Today:\n"
                    for task in todays_tasks:
                        urgency_indicator = "URGENT" if task.urgency >= 8 else "Priority" if task.urgency >= 5 else "Task"
                        message += f"• {urgency_indicator}: {task.title}\n"
                    message += "\n"
                
                message += "Have a productive day!"
            
            self._send_telegram_message(message)
            self.logger.info("Sent daily schedule digest")
            
        except Exception as e:
            self.logger.error(f"Error sending daily schedule: {e}")
    
    def send_upcoming_events(self):
        """Send upcoming events for the day"""
        if not self.telegram_chat_ids:
            return
        
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
                message = "Upcoming Events Today:\n\n"
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
    
    def send_priority_task_reminder(self):
        """Send priority task reminder"""
        if not self.telegram_chat_ids:
            return
        
        try:
            # Get top 3 priority incomplete tasks
            priority_tasks = db.session.query(Task).filter(
                Task.is_completed == False
            ).order_by(Task.urgency.desc(), Task.created_at.asc()).limit(3).all()
            
            if priority_tasks:
                message = "Focus Time! Top Priority Tasks:\n\n"
                for i, task in enumerate(priority_tasks, 1):
                    urgency_indicator = "URGENT" if task.urgency >= 8 else "Priority" if task.urgency >= 5 else "Task"
                    duration_text = f" ({task.duration}min)" if task.duration else ""
                    message += f"{i}. {urgency_indicator}: {task.title}{duration_text}\n"
                
                message += "\nPick one and make progress!"
                
                self._send_telegram_message(message)
                self.logger.info(f"Sent priority task reminder: {len(priority_tasks)} tasks")
            
        except Exception as e:
            self.logger.error(f"Error sending priority task reminder: {e}")
    
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
            
            message = f"Event Starting Soon\n\n"
            message += f"**{event.title}**\n"
            message += f"Time: {start_time}\n"
            message += f"Duration: {duration}\n"
            
            if event.location:
                message += f"Location: {event.location}\n"
            
            if event.description:
                message += f"Description: {event.description}\n"
            
            if event.is_blocking:
                message += f"Blocking Event\n"
            
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
            message = "Task Reminder\n\n"
            
            if overdue_tasks:
                message += "Overdue Tasks:\n"
                for task in overdue_tasks:
                    days_overdue = (datetime.now().date() - task.due_date).days
                    message += f"• {task.title} ({days_overdue} days overdue)\n"
                message += "\n"
            
            if high_priority_tasks:
                message += "High Priority Tasks:\n"
                for task in high_priority_tasks:
                    urgency_indicator = "URGENT" if task.urgency >= 9 else "Priority"
                    message += f"{urgency_indicator}: {task.title} (Urgency: {task.urgency})\n"
                message += "\n"
            
            message += "Stay focused and tackle these important tasks!"
            
            self._send_telegram_message(message)
            self.logger.info(f"Sent task reminder batch: {len(high_priority_tasks + overdue_tasks)} tasks")
            
        except Exception as e:
            self.logger.error(f"Error sending task reminder batch: {e}")
    
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
    
    def get_status(self):
        """Get notification service status"""
        return {
            'telegram_enabled': bool(self.telegram_bot_token),
            'registered_chats': len(self.telegram_chat_ids)
        }