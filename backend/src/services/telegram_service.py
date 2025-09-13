"""
Telegram Bot Service
NO EMOJIS
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
import asyncio
import json

from ..data.models.task_model import TaskModel, TaskStatus
from ..data.models.reminder_model import ReminderModel, ReminderStatus

logger = logging.getLogger(__name__)

class TelegramService:
    """Service for Telegram bot operations"""
    
    def __init__(self, token: str):
        self.token = token
        self.bot = Bot(token=token)
        self.application = None
        self.active_chats = set()  # Track users who have interacted with the bot
        
    async def initialize(self):
        """Initialize the Telegram application"""
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("register", self.register_command))
        self.application.add_handler(CommandHandler("current_task", self.current_task_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Start polling (for webhook, use different method)
        await self.application.initialize()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = str(update.effective_chat.id)
        self.active_chats.add(chat_id)  # Track this user
        
        await update.message.reply_text(
            "Welcome to TaskMaster Bot!\n\n"
            "You'll now receive event notifications and task reminders.\n"
            "Use /current_task to see what you should be working on."
        )
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command"""
        chat_id = str(update.effective_chat.id)
        self.active_chats.add(chat_id)  # Track this user
        
        await update.message.reply_text(
            f"Registration successful!\n\n"
            f"Your chat ID is: {chat_id}\n"
            "You'll now receive event notifications and task reminders automatically."
        )
    
    async def current_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /current_task command"""
        chat_id = str(update.effective_chat.id)
        self.active_chats.add(chat_id)  # Track this user
        
        # This would be connected to your task queue service
        await update.message.reply_text(
            "This command will show your current task once integrated with the task queue service."
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button callbacks"""
        query = update.callback_query
        await query.answer()  # Acknowledge the callback
        
        # Track this user
        chat_id = str(query.effective_chat.id)
        self.active_chats.add(chat_id)
        
        try:
            # Parse callback data
            callback_data = json.loads(query.data)
            action = callback_data.get("action")
            task_id = callback_data.get("task_id")
            reminder_id = callback_data.get("reminder_id")
            
            if action == "complete":
                await self.handle_complete_task(query, task_id, reminder_id)
            elif action == "snooze":
                await self.handle_snooze_task(query, task_id, reminder_id)
            elif action == "snooze_confirm":
                minutes = callback_data.get("minutes", 15)
                await self.handle_snooze_confirm(query, task_id, reminder_id, minutes)
            elif action == "next":
                await self.handle_next_task(query, task_id, reminder_id)
            else:
                await query.edit_message_text("Unknown action.")
                
        except Exception as e:
            logger.error(f"Error handling button callback: {e}")
            await query.edit_message_text("Error processing your request.")
    
    async def handle_complete_task(self, query, task_id: str, reminder_id: str):
        """Handle task completion"""
        try:
            from sqlalchemy.orm import sessionmaker
            from ..data.database import SessionLocal
            from .task_queue_service import TaskQueueService
            
            # Create database session
            db = SessionLocal()
            try:
                task_queue_service = TaskQueueService(db)
                success = task_queue_service.complete_task(task_id)
                
                if success:
                    await query.edit_message_text(
                        "✅ Task marked as complete!\n\n"
                        "Great work! The task has been completed and removed from your queue."
                    )
                else:
                    await query.edit_message_text(
                        "❌ Failed to complete task\n\n"
                        "There was an issue marking the task as complete. Please try again."
                    )
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}")
            await query.edit_message_text(
                "❌ Error completing task\n\n"
                "An unexpected error occurred. Please try again later."
            )
    
    async def handle_snooze_task(self, query, task_id: str, reminder_id: str):
        """Handle task snoozing"""
        # Create snooze options
        keyboard = [
            [
                InlineKeyboardButton("15 mins", callback_data=json.dumps({
                    "action": "snooze_confirm", "task_id": task_id, "reminder_id": reminder_id, "minutes": 15
                })),
                InlineKeyboardButton("30 mins", callback_data=json.dumps({
                    "action": "snooze_confirm", "task_id": task_id, "reminder_id": reminder_id, "minutes": 30
                }))
            ],
            [
                InlineKeyboardButton("1 hour", callback_data=json.dumps({
                    "action": "snooze_confirm", "task_id": task_id, "reminder_id": reminder_id, "minutes": 60
                })),
                InlineKeyboardButton("2 hours", callback_data=json.dumps({
                    "action": "snooze_confirm", "task_id": task_id, "reminder_id": reminder_id, "minutes": 120
                }))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⏰ How long would you like to snooze this task?",
            reply_markup=reply_markup
        )
    
    async def handle_snooze_confirm(self, query, task_id: str, reminder_id: str, minutes: int):
        """Handle snooze confirmation with specific duration"""
        try:
            from ..data.database import SessionLocal
            from .task_queue_service import TaskQueueService
            
            # Create database session
            db = SessionLocal()
            try:
                task_queue_service = TaskQueueService(db)
                success = task_queue_service.snooze_task(task_id, minutes)
                
                if success:
                    await query.edit_message_text(
                        f"⏰ Task snoozed for {minutes} minutes\n\n"
                        f"You'll receive a new reminder at {(datetime.now() + timedelta(minutes=minutes)).strftime('%H:%M')}."
                    )
                else:
                    await query.edit_message_text(
                        "❌ Failed to snooze task\n\n"
                        "There was an issue snoozing the task. Please try again."
                    )
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error snoozing task {task_id}: {e}")
            await query.edit_message_text(
                "❌ Error snoozing task\n\n"
                "An unexpected error occurred. Please try again later."
            )
    
    async def handle_next_task(self, query, task_id: str, reminder_id: str):
        """Handle request for next task"""
        try:
            from ..data.database import SessionLocal
            from .task_queue_service import TaskQueueService
            
            # Create database session
            db = SessionLocal()
            try:
                task_queue_service = TaskQueueService(db)
                
                # Get next task excluding the current one
                next_task_item = task_queue_service.get_next_task(exclude_task_ids=[task_id])
                
                if next_task_item:
                    next_task = next_task_item["task"]
                    
                    # Send new task reminder
                    chat_id = str(query.effective_chat.id)
                    
                    # Create a temporary reminder for the next task
                    from ..data.models.reminder_model import ReminderModel, ReminderType, ReminderStatus
                    temp_reminder = ReminderModel(
                        id="temp",
                        reminder_type=ReminderType.TASK_START,
                        title=f"Next Task: {next_task.title}",
                        message="",
                        scheduled_time=datetime.now(),
                        status=ReminderStatus.PENDING
                    )
                    
                    message_id = await self.send_task_reminder(
                        chat_id, 
                        next_task, 
                        temp_reminder,
                        f"🔄 **Next priority task:**\n\n*{next_task.title}*" + 
                        (f"\n\n{next_task.description}" if next_task.description else "") +
                        (f"\n\n⏱️ Estimated: {next_task.duration} min" if next_task.duration else "") +
                        f"\n📊 Priority score: {next_task_item['priority_score']:.1f}" +
                        ("\n⚠️ **OVERDUE**" if next_task_item['is_overdue'] else "")
                    )
                    
                    if not message_id:
                        await query.edit_message_text(
                            f"🔄 Next task found: **{next_task.title}**\n\n"
                            f"Priority score: {next_task_item['priority_score']:.1f}" +
                            ("\n⚠️ This task is overdue!" if next_task_item['is_overdue'] else "")
                        )
                    
                else:
                    await query.edit_message_text(
                        "🎉 No more tasks in your queue!\n\n"
                        "All caught up! You can take a well-deserved break or add new tasks to your list."
                    )
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting next task: {e}")
            await query.edit_message_text(
                "❌ Error finding next task\n\n"
                "An unexpected error occurred while looking for your next task."
            )
    
    async def send_task_reminder(
        self, 
        chat_id: str, 
        task: TaskModel, 
        reminder: ReminderModel,
        message: Optional[str] = None
    ) -> Optional[str]:
        """Send a task reminder with interactive buttons"""
        try:
            # Default message if none provided
            if not message:
                message = f"⏰ Time to work on:\n\n*{task.title}*"
                if task.description:
                    message += f"\n\n{task.description}"
                if task.duration:
                    message += f"\n\n⏱️ Estimated duration: {task.duration} minutes"
                if task.due_date:
                    message += f"\n📅 Due: {task.due_date}"
            
            # Create inline keyboard with action buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Mark Complete", callback_data=json.dumps({
                        "action": "complete",
                        "task_id": task.id,
                        "reminder_id": reminder.id
                    })),
                ],
                [
                    InlineKeyboardButton("⏰ Snooze Task", callback_data=json.dumps({
                        "action": "snooze",
                        "task_id": task.id,
                        "reminder_id": reminder.id
                    })),
                    InlineKeyboardButton("🔄 Work on Something Else", callback_data=json.dumps({
                        "action": "next",
                        "task_id": task.id,
                        "reminder_id": reminder.id
                    }))
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send the message
            sent_message = await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            return str(sent_message.message_id)
            
        except Exception as e:
            logger.error(f"Error sending task reminder: {e}")
            return None
    
    async def send_simple_message(self, chat_id: str, message: str) -> Optional[str]:
        """Send a simple text message"""
        try:
            sent_message = await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            return str(sent_message.message_id)
        except Exception as e:
            logger.error(f"Error sending simple message: {e}")
            return None
    
    async def send_event_notification(self, chat_id: str, event) -> Optional[str]:
        """Send an event start notification"""
        try:
            from datetime import datetime
            
            # Format the event message
            message = f"📅 **Event Starting Now:**\n\n*{event.title}*"
            
            if event.description:
                message += f"\n\n{event.description}"
            
            if event.location:
                message += f"\n\n📍 Location: {event.location}"
            
            # Add duration info
            duration = event.duration_minutes()
            if duration > 0:
                hours = duration // 60
                minutes = duration % 60
                if hours > 0:
                    duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
                else:
                    duration_str = f"{minutes}m"
                message += f"\n⏱️ Duration: {duration_str}"
            
            # Add end time
            if event.end_time:
                end_time_str = event.end_time.strftime("%H:%M")
                message += f"\n🏁 Ends at: {end_time_str}"
            
            # Add event type if not custom
            if event.event_type and event.event_type.value != 'custom':
                message += f"\n🏷️ Type: {event.event_type.value.title()}"
            
            sent_message = await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return str(sent_message.message_id)
            
        except Exception as e:
            logger.error(f"Error sending event notification: {e}")
            return None
    
    async def edit_message(self, chat_id: str, message_id: str, new_text: str) -> bool:
        """Edit an existing message"""
        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=int(message_id),
                text=new_text,
                parse_mode=ParseMode.MARKDOWN
            )
            return True
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return False
    
    async def delete_message(self, chat_id: str, message_id: str) -> bool:
        """Delete a message"""
        try:
            await self.bot.delete_message(
                chat_id=chat_id,
                message_id=int(message_id)
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return False
    
    async def get_active_chats(self) -> list[str]:
        """Get list of active chat IDs"""
        return list(self.active_chats)
    
    def start_polling(self):
        """Start the bot in polling mode (for development)"""
        if not self.application:
            raise RuntimeError("Application not initialized. Call initialize() first.")
        
        self.application.run_polling()
    
    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()

# Singleton instance
_telegram_service: Optional[TelegramService] = None

def get_telegram_service() -> Optional[TelegramService]:
    """Get the global Telegram service instance"""
    return _telegram_service

def initialize_telegram_service(token: str) -> TelegramService:
    """Initialize the global Telegram service"""
    global _telegram_service
    _telegram_service = TelegramService(token)
    return _telegram_service