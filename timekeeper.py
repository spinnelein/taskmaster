#!/usr/bin/env python3
"""
Timekeeper - Standalone Telegram Event Notification Service
Monitors the database and sends notifications when events begin.
"""

import os
import sys
import sqlite3
import logging
import asyncio
import signal
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('timekeeper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Timekeeper:
    """Standalone service for sending event start notifications via Telegram"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv('.env.production')
        
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.bot = Bot(token=self.bot_token)
        self.application = None
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # API and file paths
        self.api_base_url = "http://localhost:5000/api"
        self.db_path = Path(__file__).parent / 'taskmaster.db'
        self.chat_file = Path(__file__).parent / 'telegram_chats.txt'
        
        # Track active chat IDs
        self.active_chats = set()
        self._load_active_chats()
        
        logger.info(f"Timekeeper initialized with API: {self.api_base_url}")
        logger.info(f"Database path: {self.db_path}")
        logger.info(f"Active chats loaded: {len(self.active_chats)}")
    
    def _load_active_chats(self):
        """Load active chat IDs from file"""
        try:
            if self.chat_file.exists():
                with open(self.chat_file, 'r') as f:
                    for line in f:
                        chat_id = line.strip()
                        if chat_id:
                            self.active_chats.add(chat_id)
                logger.info(f"Loaded {len(self.active_chats)} chat IDs from {self.chat_file}")
            else:
                logger.warning(f"Chat file not found: {self.chat_file}")
        except Exception as e:
            logger.error(f"Error loading chat IDs: {e}")
    
    def _get_events_starting_now(self) -> List[Dict]:
        """Query database for events starting in the current minute"""
        try:
            # Calculate current minute window
            now = datetime.now()
            start_time = now.replace(second=0, microsecond=0)
            end_time = start_time + timedelta(minutes=1)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                cursor = conn.cursor()
                
                query = """
                SELECT * FROM events 
                WHERE start_time >= ? 
                AND start_time < ? 
                AND (notifications_enabled IS NULL OR notifications_enabled = 1)
                """
                
                cursor.execute(query, (start_time.isoformat(), end_time.isoformat()))
                events = [dict(row) for row in cursor.fetchall()]
                
                logger.debug(f"Found {len(events)} events starting at {start_time.strftime('%H:%M')}")
                return events
                
        except Exception as e:
            logger.error(f"Error querying events: {e}")
            return []
    
    def _format_event_message(self, event: Dict) -> str:
        """Format event into rich Telegram message"""
        try:
            # Start with basic info
            message = f"📅 **Event Starting Now:**\n\n*{event['title']}*"
            
            # Add description if available
            if event.get('description'):
                message += f"\n\n{event['description']}"
            
            # Add location if available
            if event.get('location'):
                message += f"\n\n📍 Location: {event['location']}"
            
            # Calculate and add duration
            if event.get('start_time') and event.get('end_time'):
                try:
                    start_dt = datetime.fromisoformat(event['start_time'])
                    end_dt = datetime.fromisoformat(event['end_time'])
                    duration = end_dt - start_dt
                    
                    total_minutes = int(duration.total_seconds() / 60)
                    if total_minutes > 0:
                        hours = total_minutes // 60
                        minutes = total_minutes % 60
                        
                        if hours > 0:
                            duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
                        else:
                            duration_str = f"{minutes}m"
                        
                        message += f"\n⏱️ Duration: {duration_str}"
                        message += f"\n🏁 Ends at: {end_dt.strftime('%H:%M')}"
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error calculating duration for event {event.get('id', 'unknown')}: {e}")
            
            # Add event type if available and not custom
            if event.get('event_type') and event['event_type'] != 'custom':
                message += f"\n🏷️ Type: {event['event_type'].title()}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting event message: {e}")
            return f"📅 **Event Starting Now:** {event.get('title', 'Unknown Event')}"
    
    async def _send_notification(self, chat_id: str, message: str) -> bool:
        """Send notification to a specific chat"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            return True
        except Exception as e:
            logger.error(f"Error sending notification to {chat_id}: {e}")
            return False
    
    async def _create_task_via_api(self, title: str) -> Optional[Dict]:
        """Create a new task via Flask API"""
        try:
            payload = {'title': title}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/tasks",
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    
                    if response.status == 200:
                        task_data = await response.json()
                        logger.info(f"Created task via API: {title} (ID: {task_data.get('id', 'unknown')[:8]})")
                        return task_data
                    else:
                        error_text = await response.text()
                        logger.error(f"API error creating task: {response.status} - {error_text}")
                        return None
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error creating task '{title}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating task '{title}': {e}")
            return None
    
    async def _test_api_connectivity(self) -> bool:
        """Test if Flask API is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url.replace('/api', '')}/health") as response:
                    if response.status == 200:
                        logger.info("API connectivity test successful")
                        return True
                    else:
                        logger.warning(f"API health check returned status {response.status}")
                        return False
        except Exception as e:
            logger.warning(f"API connectivity test failed: {e}")
            return False
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram messages"""
        try:
            chat_id = str(update.effective_chat.id)
            message_text = update.message.text.strip()
            
            # Add chat to active chats if not already there
            if chat_id not in self.active_chats:
                self.active_chats.add(chat_id)
                self._save_active_chats()
            
            logger.info(f"Received message from {chat_id}: {message_text}")
            
            # Check for "add task" command
            if message_text.lower().startswith('add task '):
                task_title = message_text[9:].strip()  # Remove "add task " prefix
                
                if task_title:
                    # Create the task via API
                    task_data = await self._create_task_via_api(task_title)
                    
                    if task_data:
                        task_id = task_data.get('id', 'unknown')
                        duration = task_data.get('duration', 30)
                        priority = task_data.get('priority', 'medium')
                        response = (
                            f"✅ **Task Created**\n\n"
                            f"*{task_title}*\n\n"
                            f"Task ID: `{task_id[:8] if task_id != 'unknown' else 'unknown'}`\n"
                            f"Duration: {duration} minutes\n"
                            f"Priority: {priority.title()}\n"
                            f"Status: Active"
                        )
                    else:
                        response = "❌ Failed to create task. Make sure the Flask app is running on port 5000."
                else:
                    response = "Please provide a task name.\nExample: `add task Buy groceries`"
                
                await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                
            elif message_text.lower() in ['/start', 'start', 'hello', 'hi']:
                response = (
                    "🕐 **Timekeeper Bot**\n\n"
                    "I'll send you notifications when events start!\n\n"
                    "**Commands:**\n"
                    "• `add task TaskName` - Create a new task\n"
                    "• Type naturally - I'll recognize commands\n\n"
                    "Your chat is now registered for notifications."
                )
                await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                
            else:
                # Unknown command
                response = (
                    "I didn't understand that command.\n\n"
                    "Try: `add task Your task name`"
                )
                await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await update.message.reply_text("Sorry, I encountered an error processing your message.")
            except:
                pass
    
    def _save_active_chats(self):
        """Save active chat IDs to file"""
        try:
            with open(self.chat_file, 'w') as f:
                for chat_id in self.active_chats:
                    f.write(f"{chat_id}\n")
            logger.info(f"Saved {len(self.active_chats)} chat IDs to {self.chat_file}")
        except Exception as e:
            logger.error(f"Error saving chat IDs: {e}")
    
    async def _start_polling(self):
        """Start Telegram bot polling in background"""
        try:
            await self.application.updater.start_polling()
            logger.info("Telegram bot started polling for messages")
        except Exception as e:
            logger.error(f"Error starting Telegram polling: {e}")
    
    async def _stop_polling(self):
        """Stop Telegram bot polling"""
        try:
            if self.application and self.application.updater:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram bot polling stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram polling: {e}")
    
    async def check_and_notify(self):
        """Main notification check - called every minute"""
        try:
            if not self.active_chats:
                logger.debug("No active chats to notify")
                return
            
            events = self._get_events_starting_now()
            if not events:
                logger.debug("No events starting now")
                return
            
            logger.info(f"Processing {len(events)} events starting now")
            
            for event in events:
                try:
                    message = self._format_event_message(event)
                    
                    # Send to all active chats
                    success_count = 0
                    for chat_id in self.active_chats:
                        if await self._send_notification(chat_id, message):
                            success_count += 1
                    
                    if success_count > 0:
                        logger.info(f"Sent notification for '{event['title']}' to {success_count} chats")
                    else:
                        logger.warning(f"Failed to send notification for '{event['title']}' to any chat")
                        
                except Exception as e:
                    logger.error(f"Error processing event '{event.get('title', 'unknown')}': {e}")
                    
        except Exception as e:
            logger.error(f"Error in check_and_notify: {e}")
    
    async def start(self):
        """Start the Timekeeper service"""
        if self.is_running:
            logger.warning("Timekeeper is already running")
            return
        
        logger.info("Starting Timekeeper service...")
        
        # Test API connectivity
        api_available = await self._test_api_connectivity()
        if not api_available:
            logger.warning("Flask API not available - task creation will not work")
        
        # Initialize Telegram application for handling messages
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add message handler for all text messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Initialize and start the application
        await self.application.initialize()
        await self.application.start()
        
        # Start polling for messages in the background
        asyncio.create_task(self._start_polling())
        
        # Schedule the notification check every minute
        self.scheduler.add_job(
            self.check_and_notify,
            trigger=IntervalTrigger(minutes=1),
            id="event_notifications",
            name="Event Start Notifications",
            replace_existing=True,
            max_instances=1
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Timekeeper service started successfully")
        logger.info("Checking for event notifications every minute...")
        logger.info("Ready to receive 'add task' commands via Telegram!")
        
        # Test notification on startup
        if self.active_chats:
            status_msg = "✅ Ready" if api_available else "⚠️ API unavailable"
            test_message = f"🤖 Timekeeper service started - {status_msg}\n\nTry: `add task Your task name`"
            for chat_id in self.active_chats:
                try:
                    await self._send_notification(chat_id, test_message)
                except:
                    pass  # Ignore test notification failures
    
    async def stop(self):
        """Stop the Timekeeper service"""
        if not self.is_running:
            logger.warning("Timekeeper is not running")
            return
        
        logger.info("Stopping Timekeeper service...")
        
        # Stop Telegram polling
        await self._stop_polling()
        
        # Shutdown the scheduler
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        
        logger.info("Timekeeper service stopped")
    
    async def run_forever(self):
        """Run the service until interrupted"""
        await self.start()
        
        try:
            # Keep running until interrupted
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop()

# Global instance for signal handling
timekeeper_instance = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if timekeeper_instance and timekeeper_instance.is_running:
        asyncio.create_task(timekeeper_instance.stop())

async def main():
    """Main entry point"""
    global timekeeper_instance
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        timekeeper_instance = Timekeeper()
        await timekeeper_instance.run_forever()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🕐 Starting Timekeeper - Event Notification Service")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Timekeeper stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)