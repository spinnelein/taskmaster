"""
Reminder repository
NO EMOJIS
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.reminder_model import ReminderModel, ReminderTemplateModel, ReminderStatus, ReminderType

class ReminderRepository(BaseRepository[ReminderModel]):
    """Repository for reminder data operations"""
    
    def __init__(self, db: Session):
        super().__init__(ReminderModel, db)
    
    def get_pending_reminders(self, limit: int = 100) -> List[ReminderModel]:
        """Get all pending reminders that are due"""
        now = datetime.now()
        
        return self.db.query(self.model).filter(
            and_(
                self.model.status == ReminderStatus.PENDING,
                self.model.scheduled_time <= now,
                # Exclude snoozed reminders that aren't ready yet
                or_(
                    self.model.snooze_until.is_(None),
                    self.model.snooze_until <= now
                )
            )
        ).order_by(self.model.scheduled_time).limit(limit).all()
    
    def get_failed_reminders(self, max_retries: int = 3) -> List[ReminderModel]:
        """Get failed reminders that can be retried"""
        return self.db.query(self.model).filter(
            and_(
                self.model.status == ReminderStatus.FAILED,
                self.model.retry_count < max_retries
            )
        ).order_by(self.model.scheduled_time).all()
    
    def get_reminders_by_task(self, task_id: str) -> List[ReminderModel]:
        """Get all reminders for a specific task"""
        return self.db.query(self.model).filter(
            self.model.task_id == task_id
        ).order_by(self.model.scheduled_time).all()
    
    def get_reminders_by_event(self, event_id: str) -> List[ReminderModel]:
        """Get all reminders for a specific event"""
        return self.db.query(self.model).filter(
            self.model.event_id == event_id
        ).order_by(self.model.scheduled_time).all()
    
    def get_reminders_by_meal(self, meal_id: str) -> List[ReminderModel]:
        """Get all reminders for a specific meal"""
        return self.db.query(self.model).filter(
            self.model.meal_id == meal_id
        ).order_by(self.model.scheduled_time).all()
    
    def get_reminders_by_chat_id(self, chat_id: str, status: Optional[ReminderStatus] = None) -> List[ReminderModel]:
        """Get reminders for a specific Telegram chat"""
        query = self.db.query(self.model).filter(
            self.model.telegram_chat_id == chat_id
        )
        
        if status:
            query = query.filter(self.model.status == status)
            
        return query.order_by(self.model.scheduled_time.desc()).all()
    
    def get_snoozed_reminders_ready(self) -> List[ReminderModel]:
        """Get snoozed reminders that are ready to be sent"""
        now = datetime.now()
        
        return self.db.query(self.model).filter(
            and_(
                self.model.status == ReminderStatus.SNOOZED,
                self.model.snooze_until <= now
            )
        ).order_by(self.model.snooze_until).all()
    
    def mark_as_sent(self, reminder_id: str, telegram_message_id: Optional[str] = None) -> bool:
        """Mark reminder as sent"""
        update_data = {
            "status": ReminderStatus.SENT,
            "sent_at": datetime.now()
        }
        
        if telegram_message_id:
            update_data["telegram_message_id"] = telegram_message_id
            
        updated = self.update(reminder_id, update_data)
        return updated is not None
    
    def mark_as_failed(self, reminder_id: str, error_message: str) -> bool:
        """Mark reminder as failed and increment retry count"""
        reminder = self.get(reminder_id)
        if not reminder:
            return False
            
        update_data = {
            "status": ReminderStatus.FAILED,
            "error_message": error_message,
            "retry_count": reminder.retry_count + 1
        }
        
        updated = self.update(reminder_id, update_data)
        return updated is not None
    
    def snooze_reminder(self, reminder_id: str, minutes: int) -> bool:
        """Snooze a reminder for specified minutes"""
        reminder = self.get(reminder_id)
        if not reminder:
            return False
            
        new_time = datetime.now() + timedelta(minutes=minutes)
        
        update_data = {
            "status": ReminderStatus.SNOOZED,
            "snooze_until": new_time,
            "snooze_count": reminder.snooze_count + 1
        }
        
        updated = self.update(reminder_id, update_data)
        return updated is not None
    
    def cancel_reminder(self, reminder_id: str) -> bool:
        """Cancel a reminder"""
        updated = self.update(reminder_id, {"status": ReminderStatus.CANCELLED})
        return updated is not None
    
    def get_upcoming_reminders(self, hours_ahead: int = 24) -> List[ReminderModel]:
        """Get upcoming reminders within specified hours"""
        now = datetime.now()
        future_time = now + timedelta(hours=hours_ahead)
        
        return self.db.query(self.model).filter(
            and_(
                self.model.status == ReminderStatus.PENDING,
                self.model.scheduled_time >= now,
                self.model.scheduled_time <= future_time
            )
        ).order_by(self.model.scheduled_time).all()
    
    def cleanup_old_reminders(self, days_old: int = 30) -> int:
        """Clean up old sent/failed reminders"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = self.db.query(self.model).filter(
            and_(
                self.model.status.in_([ReminderStatus.SENT, ReminderStatus.FAILED, ReminderStatus.CANCELLED]),
                self.model.created_at <= cutoff_date
            )
        ).delete(synchronize_session=False)
        
        self.db.commit()
        return deleted_count

class ReminderTemplateRepository(BaseRepository[ReminderTemplateModel]):
    """Repository for reminder template data operations"""
    
    def __init__(self, db: Session):
        super().__init__(ReminderTemplateModel, db)
    
    def get_active_templates(self) -> List[ReminderTemplateModel]:
        """Get all active reminder templates"""
        return self.db.query(self.model).filter(
            self.model.is_active == True
        ).order_by(self.model.name).all()
    
    def get_templates_for_tasks(self) -> List[ReminderTemplateModel]:
        """Get active templates that apply to tasks"""
        return self.db.query(self.model).filter(
            and_(
                self.model.is_active == True,
                self.model.applies_to_tasks == True
            )
        ).order_by(self.model.name).all()
    
    def get_templates_for_events(self) -> List[ReminderTemplateModel]:
        """Get active templates that apply to events"""
        return self.db.query(self.model).filter(
            and_(
                self.model.is_active == True,
                self.model.applies_to_events == True
            )
        ).order_by(self.model.name).all()
    
    def get_templates_for_meals(self) -> List[ReminderTemplateModel]:
        """Get active templates that apply to meals"""
        return self.db.query(self.model).filter(
            and_(
                self.model.is_active == True,
                self.model.applies_to_meals == True
            )
        ).order_by(self.model.name).all()
    
    def get_templates_by_type(self, reminder_type: ReminderType) -> List[ReminderTemplateModel]:
        """Get active templates of a specific type"""
        return self.db.query(self.model).filter(
            and_(
                self.model.is_active == True,
                self.model.reminder_type == reminder_type
            )
        ).order_by(self.model.name).all()
    
    def get_by_name(self, name: str) -> Optional[ReminderTemplateModel]:
        """Get template by name"""
        return self.db.query(self.model).filter(
            self.model.name == name
        ).first()
    
    def toggle_active(self, template_id: str) -> Optional[ReminderTemplateModel]:
        """Toggle the active status of a template"""
        template = self.get(template_id)
        if not template:
            return None
            
        updated = self.update(template_id, {"is_active": not template.is_active})
        return updated