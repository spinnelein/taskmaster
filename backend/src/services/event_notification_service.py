"""
Event Notification Service
NO EMOJIS
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from ..data.models.event_model import EventModel, EventStatus
from .telegram_service import get_telegram_service

logger = logging.getLogger(__name__)

class EventNotificationService:
    """Service for managing event notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.telegram_service = get_telegram_service()
        self.active_chat_ids = set()  # Track active users who have interacted with the bot
    
    async def send_event_start_notifications(self):
        """Send notifications for events starting now"""
        if not self.telegram_service:
            logger.warning("Telegram service not available")
            return
        
        # Get active chat IDs from the telegram service
        active_chats = await self.telegram_service.get_active_chats()
        if not active_chats:
            logger.info("No active chats to send event notifications to")
            return
        
        try:
            now = datetime.now()
            # Look for events starting in the current minute
            start_time = now.replace(second=0, microsecond=0)
            end_time = start_time + timedelta(minutes=1)
            
            # Find events starting now
            events = self.db.query(EventModel).filter(
                EventModel.start_time >= start_time,
                EventModel.start_time < end_time,
                EventModel.status == EventStatus.SCHEDULED,
                EventModel.notifications_enabled == True
            ).all()
            
            logger.info(f"Found {len(events)} events starting at {start_time.strftime('%H:%M')}")
            
            for event in events:
                try:
                    # Send the notification to all active chats
                    notification_sent = False
                    for chat_id in active_chats:
                        message_id = await self.telegram_service.send_event_notification(
                            chat_id, 
                            event
                        )
                        
                        if message_id:
                            logger.info(f"Sent notification for event '{event.title}' to chat {chat_id}")
                            notification_sent = True
                        else:
                            logger.error(f"Failed to send notification for event '{event.title}' to chat {chat_id}")
                    
                    # Update event status if at least one notification was sent
                    if notification_sent:
                        event.status = EventStatus.IN_PROGRESS
                        self.db.commit()
                        
                except Exception as e:
                    logger.error(f"Error sending notification for event '{event.title}' (ID: {event.id}): {e}")
                    
        except Exception as e:
            logger.error(f"Error in send_event_start_notifications: {e}")
    
    async def schedule_event_reminders(self, event_id: str) -> bool:
        """Schedule reminder notifications for an event based on its reminder_minutes_before"""
        try:
            event = self.db.query(EventModel).filter(EventModel.id == event_id).first()
            if not event:
                logger.warning(f"Event {event_id} not found")
                return False
                
            if not event.notifications_enabled:
                logger.info(f"Notifications disabled for event '{event.title}' (ID: {event_id})")
                return True
            
            if not event.reminder_minutes_before:
                logger.info(f"No reminders configured for event '{event.title}' (ID: {event_id})")
                return True
            
            # This would integrate with a scheduler like APScheduler to schedule reminder jobs
            # For now, we'll log what reminders would be scheduled
            for minutes_before in event.reminder_minutes_before:
                reminder_time = event.start_time - timedelta(minutes=minutes_before)
                if reminder_time > datetime.now():
                    logger.info(f"Would schedule reminder for '{event.title}' at {reminder_time.strftime('%Y-%m-%d %H:%M')} ({minutes_before} min before)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling reminders for event {event_id}: {e}")
            return False
    
    def get_upcoming_events(self, hours_ahead: int = 24) -> List[EventModel]:
        """Get events starting within the specified hours"""
        try:
            now = datetime.now()
            end_time = now + timedelta(hours=hours_ahead)
            
            events = self.db.query(EventModel).filter(
                EventModel.start_time >= now,
                EventModel.start_time <= end_time,
                EventModel.status.in_([EventStatus.SCHEDULED, EventStatus.CONFIRMED]),
                EventModel.notifications_enabled == True
            ).order_by(EventModel.start_time).all()
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []
    
    async def send_daily_schedule_summary(self):
        """Send a summary of today's events"""
        if not self.telegram_service:
            return
        
        # Get active chat IDs
        active_chats = await self.telegram_service.get_active_chats()
        if not active_chats:
            return
        
        try:
            # Get today's events
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            events = self.db.query(EventModel).filter(
                EventModel.start_time >= datetime.combine(today, datetime.min.time()),
                EventModel.start_time < datetime.combine(tomorrow, datetime.min.time()),
                EventModel.status.in_([EventStatus.SCHEDULED, EventStatus.CONFIRMED]),
                EventModel.notifications_enabled == True
            ).order_by(EventModel.start_time).all()
            
            if not events:
                message = f"📅 **Today's Schedule - {today.strftime('%A, %B %d')}**\n\nNo events scheduled for today."
            else:
                message = f"📅 **Today's Schedule - {today.strftime('%A, %B %d')}**\n\n"
                
                for event in events:
                    start_time = event.start_time.strftime("%H:%M")
                    duration = event.duration_minutes()
                    
                    message += f"• **{start_time}** - *{event.title}*"
                    
                    if duration > 0:
                        hours = duration // 60
                        minutes = duration % 60
                        if hours > 0:
                            duration_str = f" ({hours}h {minutes}m)" if minutes > 0 else f" ({hours}h)"
                        else:
                            duration_str = f" ({minutes}m)"
                        message += duration_str
                    
                    if event.location:
                        message += f" at {event.location}"
                    
                    message += "\n"
            
            # Send to all active chats
            for chat_id in active_chats:
                await self.telegram_service.send_simple_message(chat_id, message)
            logger.info(f"Sent daily schedule summary to {len(active_chats)} chats")
            
        except Exception as e:
            logger.error(f"Error sending daily schedule summary: {e}")