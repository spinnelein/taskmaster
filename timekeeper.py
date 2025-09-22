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
    level=logging.DEBUG,  # Changed to DEBUG to see all messages
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
        
        # Task management state
        self.current_task = None
        self.task_start_time = None
        self.pending_follow_ups = {}  # chat_id -> {task_id, assignment_id, reminder_time}
        
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
    
    async def _get_events_starting_now(self) -> List[Dict]:
        """Get events starting in the current minute via API (handles recurring events)"""
        try:
            # Calculate current minute window
            now = datetime.now()
            start_time = now.replace(second=0, microsecond=0)
            end_time = start_time + timedelta(minutes=1)
            
            # Use API to get expanded events (includes recurring event instances)
            async with aiohttp.ClientSession() as session:
                params = {
                    'mode': 'calendar',
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
                
                logger.info(f"Checking for events via API between {start_time.isoformat()} and {end_time.isoformat()}")
                
                async with session.get(
                    f"{self.api_base_url}/events",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        all_events = await response.json()
                        
                        # Filter for events with notifications enabled and starting in current minute
                        filtered_events = []
                        for event in all_events:
                            # Check if notifications are enabled (default to True if not specified)
                            notifications_enabled = event.get('notifications_enabled', True)
                            if not notifications_enabled:
                                continue
                            
                            # Parse event start time and check if it's in our window
                            event_start_str = event.get('start')
                            if event_start_str:
                                try:
                                    # Handle different datetime formats
                                    if 'T' in event_start_str:
                                        event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00')).replace(tzinfo=None)
                                    else:
                                        event_start = datetime.fromisoformat(event_start_str)
                                    
                                    # Check if event starts in current minute window
                                    if start_time <= event_start < end_time:
                                        filtered_events.append(event)
                                        
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"Could not parse event start time '{event_start_str}': {e}")
                        
                        if len(filtered_events) > 0:
                            logger.info(f"Found {len(filtered_events)} events starting at {start_time.strftime('%H:%M')}")
                            for event in filtered_events:
                                logger.info(f"Event: {event.get('title', 'Unknown')} starts at {event.get('start', 'Unknown time')}")
                        else:
                            logger.debug(f"No events found for {start_time.strftime('%H:%M')}")
                        
                        return filtered_events
                    
                    else:
                        logger.error(f"API error getting events: {response.status}")
                        return []
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error getting events from API: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting events from API: {e}", exc_info=True)
            return []
    
    def _format_event_message(self, event: Dict) -> str:
        """Format event into rich Telegram message"""
        try:
            # Start with basic info
            title = event.get('title', 'Unknown Event')
            message = f"🔔 **Event Starting Now:**\n\n*{title}*"
            
            # Add description if available
            if event.get('description'):
                message += f"\n\n{event['description']}"
            
            # Add location if available
            if event.get('location'):
                message += f"\n\n📍 Location: {event['location']}"
            
            # Calculate and add duration using API response format
            start_time_str = event.get('start') or event.get('start_time')
            end_time_str = event.get('end') or event.get('end_time')
            
            if start_time_str and end_time_str:
                try:
                    # Handle different datetime formats from API
                    if 'T' in start_time_str:
                        start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    else:
                        start_dt = datetime.fromisoformat(start_time_str)
                    
                    if 'T' in end_time_str:
                        end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    else:
                        end_dt = datetime.fromisoformat(end_time_str)
                    
                    duration = end_dt - start_dt
                    total_minutes = int(duration.total_seconds() / 60)
                    
                    if total_minutes > 0:
                        hours = total_minutes // 60
                        minutes = total_minutes % 60
                        
                        if hours > 0:
                            duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
                        else:
                            duration_str = f"{minutes}m"
                        
                        message += f"\n\n⏱️ Duration: {duration_str}"
                        message += f"\n🏁 Ends at: {end_dt.strftime('%I:%M %p')}"
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error calculating duration for event {event.get('id', 'unknown')}: {e}")
            
            # Add event type if available and not custom
            event_type = event.get('event_type')
            if event_type and event_type != 'custom':
                message += f"\n\n📋 Type: {event_type.title()}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting event message: {e}")
            return f"🔔 **Event Starting Now:** {event.get('title', 'Unknown Event')}"
    
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
    
    async def _get_current_task_from_schedule(self) -> Optional[Dict]:
        """Get the first incomplete task from today's schedule"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            async with aiohttp.ClientSession() as session:
                # Get today's assignments
                async with session.get(
                    f"{self.api_base_url}/assignments_api",
                    params={
                        'start_date': today,
                        'end_date': today
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        assignments = result.get('assignments', [])
                        
                        # Check assignments one by one until we find an incomplete task
                        for assignment in assignments:
                            task_id = assignment.get('task_id')
                            if not task_id:
                                continue
                                
                            # Check this task's completion status
                            try:
                                async with session.get(
                                    f"{self.api_base_url}/tasks/{task_id}",
                                    timeout=aiohttp.ClientTimeout(total=5)
                                ) as task_response:
                                    
                                    if task_response.status == 200:
                                        task_data = await task_response.json()
                                        task_status = task_data.get('status', 'active')
                                        is_snoozed = task_data.get('is_snoozed', False)
                                        
                                        # Skip completed and snoozed tasks
                                        if task_status not in ['completed', 'snoozed'] and not is_snoozed:
                                            # Found first available task - return it
                                            logger.debug(f"Found available task: {assignment.get('task_title', 'Unknown')} (ID: {task_id[:8]}, status: {task_status})")
                                            return assignment
                                        else:
                                            logger.debug(f"Task {assignment.get('task_title', 'Unknown')} is {task_status}/snoozed={is_snoozed}, checking next")
                                    else:
                                        logger.warning(f"Could not check task {task_id}: {task_response.status}")
                                        
                            except Exception as e:
                                logger.warning(f"Error checking task {task_id}: {e}")
                                continue
                        
                        logger.debug("All tasks in today's schedule are completed")
                        return None
                    else:
                        logger.error(f"API error getting assignments: {response.status}")
                        return None
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error getting assignments: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting assignments: {e}")
            return None
    
    def _format_current_task_message(self, assignment: Dict) -> str:
        """Format current scheduled task message"""
        try:
            title = assignment.get('task_title', 'Unknown Task')
            message = f"📋 **Current Task:**\n\n*{title}*"
            
            # Add time pool details
            pool_date = assignment.get('pool_date')
            pool_start = assignment.get('pool_start_time')
            pool_end = assignment.get('pool_end_time')
            
            # Add allocated time
            allocated_minutes = assignment.get('allocated_minutes')
            if allocated_minutes:
                hours = allocated_minutes // 60
                minutes = allocated_minutes % 60
                if hours > 0:
                    duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
                else:
                    duration_str = f"{minutes}m"
                message += f"\n⏱️ Duration: {duration_str}"
            
            # Add priority if available
            priority = assignment.get('task_priority')
            if priority:
                message += f"\n🔥 Priority: {priority.title()}"
            
            # Add assignment status
            status = assignment.get('status', 'assigned')
            if status != 'assigned':
                message += f"\n📊 Status: {status.replace('_', ' ').title()}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting current task message: {e}")
            return f"📋 **Current Task:** {assignment.get('task_title', 'Unknown Task')}"
    
    async def _start_task_tracking(self, assignment: Dict, chat_id: str):
        """Start tracking a task and schedule follow-up"""
        try:
            self.current_task = assignment
            self.task_start_time = datetime.now()
            
            # Schedule follow-up after task duration
            allocated_minutes = assignment.get('allocated_minutes', 30)
            follow_up_time = self.task_start_time + timedelta(minutes=allocated_minutes)
            
            # Store follow-up for this chat
            self.pending_follow_ups[chat_id] = {
                'task_id': assignment.get('task_id'),
                'assignment_id': assignment.get('id'),
                'task_title': assignment.get('task_title'),
                'follow_up_time': follow_up_time,
                'allocated_minutes': allocated_minutes
            }
            
            logger.info(f"Started tracking task '{assignment.get('task_title')}' for {allocated_minutes} minutes")
            
            # Schedule the follow-up check
            self.scheduler.add_job(
                self._send_task_follow_up,
                'date',
                run_date=follow_up_time,
                args=[chat_id],
                id=f"task_followup_{chat_id}_{assignment.get('id')}",
                replace_existing=True
            )
            
        except Exception as e:
            logger.error(f"Error starting task tracking: {e}")
    
    async def _send_task_follow_up(self, chat_id: str):
        """Send follow-up message after task duration"""
        try:
            follow_up = self.pending_follow_ups.get(chat_id)
            if not follow_up:
                return
            
            # Check if we're still in available time pool
            if not await self._is_currently_in_available_time_pool():
                logger.info(f"Task follow-up cancelled - outside work hours for '{follow_up.get('task_title', 'Unknown')}'")
                # Clear task tracking silently since work time is over
                self.current_task = None
                self.task_start_time = None
                if chat_id in self.pending_follow_ups:
                    del self.pending_follow_ups[chat_id]
                return
            
            task_title = follow_up['task_title']
            allocated_minutes = follow_up['allocated_minutes']
            
            message = (
                f"⏰ **Time's up!** ({allocated_minutes} minutes)\n\n"
                f"How's it going with: *{task_title}*?\n\n"
                f"Reply with:\n"
                f"• `completed` - Mark as done, get next task\n"
                f"• `still working` - Check again in 1 hour\n"
                f"• `something else` - When should I remind you?"
            )
            
            await self._send_notification(chat_id, message)
            logger.info(f"Sent task follow-up for '{task_title}' to {chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending task follow-up: {e}")
    
    async def _handle_task_completion(self, chat_id: str, task_id: str):
        """Handle task completion and get next task"""
        try:
            # Get completed task name before clearing tracking
            completed_task_name = self.pending_follow_ups.get(chat_id, {}).get('task_title', 'Unknown Task')
            
            # Check if task is divisible to determine completion flow
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/tasks/{task_id}") as task_response:
                    if task_response.status == 200:
                        task_data = await task_response.json()
                        is_divisible = task_data.get('is_divisible', False)
                        
                        if is_divisible:
                            # For divisible tasks, ask follow-up question
                            message = (
                                f"✅ **Chunk completed:** {completed_task_name}\n\n"
                                f"Is this task:\n"
                                f"• `completed` - Fully finished, mark as done\n"
                                f"• `done for now` - More work needed later, snooze for 11 hours"
                            )
                            await self._send_notification(chat_id, message)
                            
                            # Store task info for follow-up response
                            self.pending_follow_ups[chat_id] = {
                                'type': 'divisible_completion',
                                'task_id': task_id,
                                'task_title': completed_task_name,
                                'follow_up_time': datetime.now()
                            }
                            return  # Don't process further until user responds
                        
                        else:
                            # For non-divisible tasks, mark as completed immediately
                            await self._complete_task_fully(chat_id, task_id, completed_task_name, session)
                    else:
                        logger.warning(f"Could not get task data for {task_id}: {task_response.status}")
                        # Default to full completion if we can't check divisibility
                        await self._complete_task_fully(chat_id, task_id, completed_task_name, session)
                
        except Exception as e:
            logger.error(f"Error handling task completion: {e}")
    
    async def _complete_task_fully(self, chat_id: str, task_id: str, completed_task_name: str, session: aiohttp.ClientSession = None):
        """Complete a task fully and get next task"""
        try:
            # Create session if not provided
            if session is None:
                async with aiohttp.ClientSession() as new_session:
                    await self._mark_task_completed(task_id, new_session)
            else:
                await self._mark_task_completed(task_id, session)
            
            # Clear current task tracking
            self.current_task = None
            self.task_start_time = None
            if chat_id in self.pending_follow_ups:
                del self.pending_follow_ups[chat_id]
            
            # Get next task
            next_assignment = await self._get_current_task_from_schedule()
            if next_assignment:
                message = f"✅ **Task completed:** {completed_task_name}\n\nNext task:\n\n" + self._format_current_task_message(next_assignment)
                await self._send_notification(chat_id, message)
                
                # Start tracking the next task
                await self._start_task_tracking(next_assignment, chat_id)
            else:
                message = f"✅ **Task completed:** {completed_task_name}\n\n**All done!** No more tasks scheduled for today. Great work! 🎉"
                await self._send_notification(chat_id, message)
                
        except Exception as e:
            logger.error(f"Error in _complete_task_fully: {e}")
    
    async def _mark_task_completed(self, task_id: str, session: aiohttp.ClientSession):
        """Mark a task as completed via API"""
        try:
            async with session.post(f"{self.api_base_url}/tasks/{task_id}/complete") as response:
                if response.status == 200:
                    logger.info(f"Marked task {task_id} as completed")
                else:
                    logger.warning(f"Failed to mark task as completed: {response.status}")
        except Exception as e:
            logger.error(f"Error marking task as completed: {e}")
    
    async def _handle_done_for_now(self, chat_id: str, task_id: str, task_title: str):
        """Handle 'done for now' response - snooze task for 11 hours"""
        try:
            # Calculate new start date (11 hours from now)
            new_start_date = datetime.now() + timedelta(hours=11)
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    'start_date': new_start_date.isoformat()
                }
                
                async with session.put(
                    f"{self.api_base_url}/tasks/{task_id}",
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Deferred task {task_id} start date to {new_start_date.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        logger.warning(f"Failed to defer task: {response.status}")
            
            # Clear current task tracking
            self.current_task = None
            self.task_start_time = None
            if chat_id in self.pending_follow_ups:
                del self.pending_follow_ups[chat_id]
            
            # Small delay to ensure database update is complete
            await asyncio.sleep(1.5)
            
            # Get next task
            next_assignment = await self._get_current_task_from_schedule()
            if next_assignment:
                message = f"💤 **Task snoozed:** {task_title} (11 hours)\n\nNext task:\n\n" + self._format_current_task_message(next_assignment)
                await self._send_notification(chat_id, message)
                
                # Start tracking the next task
                await self._start_task_tracking(next_assignment, chat_id)
            else:
                message = f"💤 **Task snoozed:** {task_title} (11 hours)\n\n**All done!** No more tasks scheduled for today. Great work! 🎉"
                await self._send_notification(chat_id, message)
                
        except Exception as e:
            logger.error(f"Error handling done for now: {e}")
    
    async def _handle_still_working(self, chat_id: str):
        """Handle 'still working' response - check again in 1 hour"""
        try:
            follow_up = self.pending_follow_ups.get(chat_id)
            if not follow_up:
                return
            
            # Schedule another check in 1 hour
            next_check = datetime.now() + timedelta(hours=1)
            follow_up['follow_up_time'] = next_check
            
            self.scheduler.add_job(
                self._send_task_follow_up,
                'date',
                run_date=next_check,
                args=[chat_id],
                id=f"task_followup_{chat_id}_{follow_up.get('assignment_id')}",
                replace_existing=True
            )
            
            message = "👍 **Got it!** I'll check back with you in 1 hour. Keep up the good work!"
            await self._send_notification(chat_id, message)
            
        except Exception as e:
            logger.error(f"Error handling still working response: {e}")
    
    async def _handle_custom_reminder(self, chat_id: str, reminder_text: str):
        """Handle custom reminder timing"""
        try:
            # Parse common time formats
            reminder_minutes = None
            text_lower = reminder_text.lower()
            
            if '15' in text_lower and 'min' in text_lower:
                reminder_minutes = 15
            elif '30' in text_lower and 'min' in text_lower:
                reminder_minutes = 30
            elif '1' in text_lower and ('hour' in text_lower or 'hr' in text_lower):
                reminder_minutes = 60
            elif '2' in text_lower and ('hour' in text_lower or 'hr' in text_lower):
                reminder_minutes = 120
            
            if reminder_minutes:
                follow_up = self.pending_follow_ups.get(chat_id)
                if follow_up:
                    # Schedule reminder
                    next_reminder = datetime.now() + timedelta(minutes=reminder_minutes)
                    
                    self.scheduler.add_job(
                        self._send_current_task_reminder,
                        'date',
                        run_date=next_reminder,
                        args=[chat_id],
                        id=f"custom_reminder_{chat_id}_{follow_up.get('assignment_id')}",
                        replace_existing=True
                    )
                    
                    message = f"⏰ **Reminder set!** I'll check back in {reminder_minutes} minutes."
                    await self._send_notification(chat_id, message)
            else:
                message = (
                    "⚠️ I didn't understand the timing. Please try:\n"
                    "• `15 min` or `30 min`\n"
                    "• `1 hour` or `2 hours`"
                )
                await self._send_notification(chat_id, message)
                
        except Exception as e:
            logger.error(f"Error handling custom reminder: {e}")
    
    async def _send_current_task_reminder(self, chat_id: str):
        """Send reminder about current task"""
        try:
            follow_up = self.pending_follow_ups.get(chat_id)
            if follow_up:
                task_title = follow_up['task_title']
                message = f"🔔 **Reminder:** Are you still working on *{task_title}*?"
                await self._send_notification(chat_id, message)
                
        except Exception as e:
            logger.error(f"Error sending current task reminder: {e}")
    
    async def _is_currently_in_available_time_pool(self) -> bool:
        """Check if current time is within a scheduled time pool"""
        try:
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            current_time = now.time()
            
            # Get today's assignments to check time pools
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/assignments_api",
                    params={
                        'start_date': today,
                        'end_date': today
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        assignments = result.get('assignments', [])
                        
                        # Check if current time falls within any time pool
                        for assignment in assignments:
                            pool_start_str = assignment.get('pool_start_time')
                            pool_end_str = assignment.get('pool_end_time')
                            pool_date = assignment.get('pool_date')
                            
                            if pool_start_str and pool_end_str and pool_date == today:
                                try:
                                    # Parse pool times
                                    pool_start = datetime.strptime(pool_start_str, '%H:%M').time()
                                    pool_end = datetime.strptime(pool_end_str, '%H:%M').time()
                                    
                                    # Check if current time is within this pool
                                    if pool_start <= current_time < pool_end:
                                        logger.debug(f"Currently in time pool: {pool_start_str}-{pool_end_str}")
                                        return True
                                        
                                except ValueError as e:
                                    logger.warning(f"Error parsing pool times {pool_start_str}-{pool_end_str}: {e}")
                        
                        logger.debug(f"Current time {current_time.strftime('%H:%M')} not in any active time pool")
                        return False
                    else:
                        logger.warning(f"Could not get assignments: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error checking if in available time pool: {e}")
            return False
    
    async def _send_current_task_if_available(self):
        """Send current task notification if we're in available time and no task is being tracked"""
        try:
            # Only send if we're not already tracking a task
            if self.current_task is not None:
                logger.debug("Already tracking a task, not sending new task")
                return
            
            # Check if we're in available time
            if not await self._is_currently_in_available_time_pool():
                logger.debug("Not in available time pool, not sending task")
                return
            
            # Get current task from schedule
            assignment = await self._get_current_task_from_schedule()
            if not assignment:
                logger.debug("No tasks available in current schedule")
                return
            
            # Send to all active chats
            message = "🎯 **Time to work!** Here's your current task:\n\n" + self._format_current_task_message(assignment)
            
            for chat_id in self.active_chats:
                try:
                    await self._send_notification(chat_id, message)
                    # Start tracking this task for this chat
                    await self._start_task_tracking(assignment, chat_id)
                    logger.info(f"Automatically sent current task '{assignment.get('task_title')}' to {chat_id}")
                except Exception as e:
                    logger.error(f"Error sending current task to {chat_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in _send_current_task_if_available: {e}")
    
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
                            f"[SUCCESS] **Task Created**\n\n"
                            f"*{task_title}*\n\n"
                            f"Task ID: `{task_id[:8] if task_id != 'unknown' else 'unknown'}`\n"
                            f"Duration: {duration} minutes\n"
                            f"Priority: {priority.title()}\n"
                            f"Status: Active"
                        )
                    else:
                        response = "[ERROR] Failed to create task. Make sure the Flask app is running on port 5000."
                else:
                    response = "Please provide a task name.\nExample: `add task Buy groceries`"
                
                await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                
            elif message_text.lower() in ['current task', 'what should i work on', 'top task', 'task recommendation', '/task']:
                # Get current scheduled task
                assignment = await self._get_current_task_from_schedule()
                
                if assignment:
                    response = self._format_current_task_message(assignment)
                    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                    
                    # Start tracking this task
                    await self._start_task_tracking(assignment, chat_id)
                else:
                    response = "📋 **No tasks scheduled right now.**\n\nCheck your schedule or all tasks may be completed! 🎉"
                    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
            elif message_text.lower() in ['completed', 'done', 'finished']:
                # Handle task completion or divisible task follow-up
                follow_up = self.pending_follow_ups.get(chat_id)
                if follow_up:
                    if follow_up.get('type') == 'divisible_completion':
                        # This is a response to divisible task question - complete fully
                        await self._complete_task_fully(chat_id, follow_up['task_id'], follow_up['task_title'], None)
                    else:
                        # Regular task completion
                        await self._handle_task_completion(chat_id, follow_up['task_id'])
                else:
                    response = "✅ Great! But I'm not currently tracking a task for you. Use `current task` to get started."
                    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
            elif message_text.lower() in ['done for now', 'done for today', 'pause task']:
                # Handle divisible task snoozing specifically for divisible completion flow
                follow_up = self.pending_follow_ups.get(chat_id)
                if follow_up and follow_up.get('type') == 'divisible_completion':
                    await self._handle_done_for_now(chat_id, follow_up['task_id'], follow_up['task_title'])
                else:
                    response = "💤 This command is for divisible tasks. Try `snooze` to pause any task."
                    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
            elif message_text.lower() in ['snooze', 'snooze task', 'pause for today']:
                # Universal snooze handler - works for any currently tracked task
                follow_up = self.pending_follow_ups.get(chat_id)
                if follow_up:
                    task_id = follow_up.get('task_id')
                    task_title = follow_up.get('task_title', 'Unknown Task')
                    if task_id:
                        await self._handle_done_for_now(chat_id, task_id, task_title)
                else:
                    response = "💤 I'm not currently tracking a task for you. Use `current task` to get started."
                    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
            elif message_text.lower() in ['still working', 'not done', 'working on it', 'still on it']:
                # Handle still working response
                follow_up = self.pending_follow_ups.get(chat_id)
                if follow_up:
                    await self._handle_still_working(chat_id)
                else:
                    response = "👍 Got it! Use `current task` if you need a task reminder."
                    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
            
            elif message_text.lower() in ['something else', 'other', 'custom time', 'different time']:
                # Handle "something else" response - prompt for custom timing
                follow_up = self.pending_follow_ups.get(chat_id)
                if follow_up:
                    response = (
                        "⏰ **Custom reminder**: When should I check back?\n\n"
                        "Try:\n"
                        "• `15 min`\n"
                        "• `30 min`\n"
                        "• `1 hour`\n"
                        "• `2 hours`"
                    )
                    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                else:
                    response = "⏰ I'm not currently tracking a task for you. Use `current task` to get started."
                    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                
            elif 'min' in message_text.lower() or 'hour' in message_text.lower():
                # Handle custom reminder timing
                await self._handle_custom_reminder(chat_id, message_text)
                
            elif message_text.lower() in ['/start', 'start', 'hello', 'hi']:
                response = (
                    "🕐 **Timekeeper Bot**\n\n"
                    "I'll send you notifications when events start and help manage your daily tasks!\n\n"
                    "**Task Management:**\n"
                    "• `current task` - Get your current scheduled task\n"
                    "• `completed` - Mark current task as done\n"
                    "• `still working` - Get 1 hour extension\n"
                    "• `30 min` / `1 hour` - Custom reminder timing\n\n"
                    "**Other Commands:**\n"
                    "• `add task TaskName` - Create a new task\n"
                    "• I'll automatically track task duration and follow up!\n\n"
                    "Your chat is now registered for notifications. 🔔"
                )
                await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
                
            else:
                # Unknown command
                response = (
                    "I didn't understand that command.\n\n"
                    "**Try:**\n"
                    "• `current task` - Get your scheduled task\n"
                    "• `add task Your task name` - Create task\n"
                    "• `hello` - See all commands\n"
                    "• `completed` / `still working` - Task responses"
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
            
            # Check for event notifications first
            events = await self._get_events_starting_now()
            if events:
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
                            logger.info(f"Sent notification for '{event.get('title', 'Unknown')}' to {success_count} chats")
                        else:
                            logger.warning(f"Failed to send notification for '{event.get('title', 'Unknown')}' to any chat")
                            
                    except Exception as e:
                        logger.error(f"Error processing event '{event.get('title', 'unknown')}': {e}")
            
            # Check if we should send current task (only if no events and no current task)
            if not events:
                await self._send_current_task_if_available()
                    
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
        
        # Send startup notification and check for current task
        if self.active_chats:
            status_msg = "[READY]" if api_available else "[WARNING] API unavailable"
            test_message = f"[BOT] Timekeeper service started - {status_msg}\n\nTry: `add task Your task name`"
            for chat_id in self.active_chats:
                try:
                    await self._send_notification(chat_id, test_message)
                except:
                    pass  # Ignore test notification failures
            
            # Check if we should send current task (only if API is available)
            if api_available:
                # Schedule task check for 2 seconds after startup to avoid blocking
                self.scheduler.add_job(
                    self._send_current_task_if_available,
                    'date',
                    run_date=datetime.now() + timedelta(seconds=2),
                    id='startup_task_check'
                )
    
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
    print("[CLOCK] Starting Timekeeper - Event Notification Service")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Timekeeper stopped")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        sys.exit(1)