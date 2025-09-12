"""
Reminder Service
NO EMOJIS
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..data.models.reminder_model import ReminderModel, ReminderTemplateModel, ReminderType, ReminderStatus
from ..data.models.task_model import TaskModel, TaskStatus
from ..data.models.event_model import EventModel
from ..data.models.meal_model import MealModel
from ..data.repositories.base import BaseRepository
from .telegram_service import get_telegram_service

logger = logging.getLogger(__name__)

class ReminderService:
    """Service for managing reminders and notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.reminder_repo = BaseRepository(ReminderModel, db)
        self.template_repo = BaseRepository(ReminderTemplateModel, db)
        
    def create_task_reminder(
        self, 
        task: TaskModel, 
        reminder_type: ReminderType = ReminderType.TASK_START,
        minutes_before: int = 0,
        custom_message: Optional[str] = None,
        telegram_chat_id: Optional[str] = None
    ) -> ReminderModel:
        """Create a reminder for a task"""
        
        # Calculate scheduled time
        if task.due_date and task.due_time:
            base_time = datetime.combine(task.due_date, task.due_time)
        elif task.due_date:
            # Default to start of day if no time specified
            base_time = datetime.combine(task.due_date, datetime.min.time().replace(hour=9))
        else:
            # No due date, schedule for immediate notification
            base_time = datetime.now()
            
        scheduled_time = base_time - timedelta(minutes=minutes_before)
        
        # Generate message using template or custom message
        if custom_message:
            message = custom_message
        else:
            message = self._generate_task_message(task, reminder_type)
            
        # Create reminder
        reminder_data = {
            "reminder_type": reminder_type,
            "title": f"Task: {task.title}",
            "message": message,
            "scheduled_time": scheduled_time,
            "minutes_before": minutes_before,
            "task_id": task.id,
            "telegram_chat_id": telegram_chat_id,
            "status": ReminderStatus.PENDING
        }
        
        return self.reminder_repo.create(reminder_data)
    
    def create_event_reminder(
        self,
        event: EventModel,
        reminder_type: ReminderType = ReminderType.EVENT_START,
        minutes_before: int = 15,
        custom_message: Optional[str] = None,
        telegram_chat_id: Optional[str] = None
    ) -> ReminderModel:
        """Create a reminder for an event"""
        
        scheduled_time = event.start_time - timedelta(minutes=minutes_before)
        
        if custom_message:
            message = custom_message
        else:
            message = self._generate_event_message(event, reminder_type)
            
        reminder_data = {
            "reminder_type": reminder_type,
            "title": f"Event: {event.title}",
            "message": message,
            "scheduled_time": scheduled_time,
            "minutes_before": minutes_before,
            "event_id": event.id,
            "telegram_chat_id": telegram_chat_id,
            "status": ReminderStatus.PENDING
        }
        
        return self.reminder_repo.create(reminder_data)
    
    def create_meal_reminder(
        self,
        meal: MealModel,
        reminder_type: ReminderType = ReminderType.MEAL_PREP,
        minutes_before: int = 30,
        custom_message: Optional[str] = None,
        telegram_chat_id: Optional[str] = None
    ) -> ReminderModel:
        """Create a reminder for meal preparation"""
        
        # Assuming meal has a scheduled_time or we use event start time
        if hasattr(meal, 'scheduled_time') and meal.scheduled_time:
            base_time = meal.scheduled_time
        else:
            # Fallback to current time + some buffer
            base_time = datetime.now() + timedelta(hours=1)
            
        scheduled_time = base_time - timedelta(minutes=minutes_before)
        
        if custom_message:
            message = custom_message
        else:
            message = self._generate_meal_message(meal, reminder_type)
            
        reminder_data = {
            "reminder_type": reminder_type,
            "title": f"Meal: {meal.name}",
            "message": message,
            "scheduled_time": scheduled_time,
            "minutes_before": minutes_before,
            "meal_id": meal.id,
            "telegram_chat_id": telegram_chat_id,
            "status": ReminderStatus.PENDING
        }
        
        return self.reminder_repo.create(reminder_data)
    
    def get_pending_reminders(self, limit: int = 100) -> List[ReminderModel]:
        """Get all pending reminders that are due"""
        now = datetime.now()
        
        reminders = self.db.query(ReminderModel).filter(
            ReminderModel.status == ReminderStatus.PENDING,
            ReminderModel.scheduled_time <= now,
            # Exclude snoozed reminders
            (ReminderModel.snooze_until.is_(None)) | 
            (ReminderModel.snooze_until <= now)
        ).order_by(ReminderModel.scheduled_time).limit(limit).all()
        
        return reminders
    
    async def send_reminder(self, reminder: ReminderModel) -> bool:
        """Send a reminder via Telegram"""
        telegram_service = get_telegram_service()
        if not telegram_service:
            logger.error("Telegram service not initialized")
            return False
            
        try:
            # Determine chat ID
            chat_id = reminder.telegram_chat_id or telegram_service.default_chat_id
            if not chat_id:
                logger.error(f"No chat ID available for reminder {reminder.id}")
                return False
            
            message_id = None
            
            # Send appropriate message based on reminder type
            if reminder.task_id:
                task = self.db.query(TaskModel).filter(TaskModel.id == reminder.task_id).first()
                if task:
                    message_id = await telegram_service.send_task_reminder(
                        chat_id, task, reminder, reminder.message
                    )
            else:
                # Simple message for events/meals
                message_id = await telegram_service.send_simple_message(chat_id, reminder.message)
            
            if message_id:
                # Update reminder status
                self.reminder_repo.update(reminder.id, {
                    "status": ReminderStatus.SENT,
                    "sent_at": datetime.now(),
                    "telegram_message_id": message_id
                })
                return True
            else:
                # Mark as failed
                self.reminder_repo.update(reminder.id, {
                    "status": ReminderStatus.FAILED,
                    "error_message": "Failed to send message",
                    "retry_count": reminder.retry_count + 1
                })
                return False
                
        except Exception as e:
            logger.error(f"Error sending reminder {reminder.id}: {e}")
            # Mark as failed
            self.reminder_repo.update(reminder.id, {
                "status": ReminderStatus.FAILED,
                "error_message": str(e),
                "retry_count": reminder.retry_count + 1
            })
            return False
    
    def snooze_reminder(self, reminder_id: str, minutes: int) -> bool:
        """Snooze a reminder for specified minutes"""
        try:
            new_time = datetime.now() + timedelta(minutes=minutes)
            
            updated = self.reminder_repo.update(reminder_id, {
                "snooze_until": new_time,
                "snooze_count": self.db.query(ReminderModel).filter(
                    ReminderModel.id == reminder_id
                ).first().snooze_count + 1,
                "status": ReminderStatus.SNOOZED
            })
            
            return updated is not None
            
        except Exception as e:
            logger.error(f"Error snoozing reminder {reminder_id}: {e}")
            return False
    
    def cancel_reminder(self, reminder_id: str) -> bool:
        """Cancel a reminder"""
        try:
            updated = self.reminder_repo.update(reminder_id, {
                "status": ReminderStatus.CANCELLED
            })
            return updated is not None
        except Exception as e:
            logger.error(f"Error cancelling reminder {reminder_id}: {e}")
            return False
    
    def _generate_task_message(self, task: TaskModel, reminder_type: ReminderType) -> str:
        """Generate message for task reminders"""
        if reminder_type == ReminderType.TASK_START:
            message = f"⏰ Time to start working on: *{task.title}*"
        elif reminder_type == ReminderType.TASK_DUE:
            message = f"⚠️ Task due soon: *{task.title}*"
        else:
            message = f"📝 Task reminder: *{task.title}*"
            
        if task.description:
            message += f"\n\n{task.description}"
            
        if task.duration:
            message += f"\n\n⏱️ Estimated duration: {task.duration} minutes"
            
        if task.due_date:
            message += f"\n📅 Due: {task.due_date}"
            
        return message
    
    def _generate_event_message(self, event: EventModel, reminder_type: ReminderType) -> str:
        """Generate message for event reminders"""
        if reminder_type == ReminderType.EVENT_START:
            message = f"📅 Event starting soon: *{event.title}*"
        elif reminder_type == ReminderType.EVENT_PREP:
            message = f"🎯 Time to prepare for: *{event.title}*"
        else:
            message = f"📅 Event reminder: *{event.title}*"
            
        message += f"\n\n🕐 Start time: {event.start_time.strftime('%H:%M')}"
        
        if event.location:
            message += f"\n📍 Location: {event.location}"
            
        if event.description:
            message += f"\n\n{event.description}"
            
        return message
    
    def _generate_meal_message(self, meal: MealModel, reminder_type: ReminderType) -> str:
        """Generate message for meal reminders"""
        if reminder_type == ReminderType.MEAL_PREP:
            message = f"👨‍🍳 Time to start preparing: *{meal.name}*"
        else:
            message = f"🍽️ Meal reminder: *{meal.name}*"
            
        if meal.estimated_prep_time_minutes:
            message += f"\n\n⏱️ Prep time: {meal.estimated_prep_time_minutes} minutes"
            
        return message
    
    def create_template_based_reminders(self, entity, entity_type: str) -> List[ReminderModel]:
        """Create reminders based on active templates"""
        reminders = []
        
        # Get active templates for this entity type
        templates = self.db.query(ReminderTemplateModel).filter(
            ReminderTemplateModel.is_active == True
        )
        
        if entity_type == "task":
            templates = templates.filter(ReminderTemplateModel.applies_to_tasks == True)
        elif entity_type == "event":
            templates = templates.filter(ReminderTemplateModel.applies_to_events == True)
        elif entity_type == "meal":
            templates = templates.filter(ReminderTemplateModel.applies_to_meals == True)
            
        for template in templates.all():
            try:
                # Create reminder based on template
                if entity_type == "task":
                    reminder = self.create_task_reminder(
                        entity,
                        template.reminder_type,
                        template.default_minutes_before,
                        template.message_template.format(task_title=entity.title)
                    )
                elif entity_type == "event":
                    reminder = self.create_event_reminder(
                        entity,
                        template.reminder_type,
                        template.default_minutes_before,
                        template.message_template.format(event_title=entity.title)
                    )
                elif entity_type == "meal":
                    reminder = self.create_meal_reminder(
                        entity,
                        template.reminder_type,
                        template.default_minutes_before,
                        template.message_template.format(meal_name=entity.name)
                    )
                
                reminders.append(reminder)
                
            except Exception as e:
                logger.error(f"Error creating reminder from template {template.id}: {e}")
                
        return reminders