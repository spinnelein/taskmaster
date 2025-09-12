"""
Background worker for processing reminders
NO EMOJIS
"""
import logging
import asyncio
from typing import Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import sessionmaker

from ..services.reminder_service import ReminderService
from ..data.repositories.reminder_repo import ReminderRepository
from ..data.models.reminder_model import ReminderStatus

logger = logging.getLogger(__name__)

class ReminderWorker:
    """Background worker for processing reminder notifications"""
    
    def __init__(self, db_session_factory: sessionmaker):
        self.db_session_factory = db_session_factory
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    async def start(self):
        """Start the reminder worker"""
        if self.is_running:
            logger.warning("Reminder worker is already running")
            return
            
        logger.info("Starting reminder worker...")
        
        # Schedule reminder processing every minute
        self.scheduler.add_job(
            self.process_pending_reminders,
            trigger=IntervalTrigger(minutes=1),
            id="process_pending_reminders",
            name="Process Pending Reminders",
            replace_existing=True,
            max_instances=1  # Prevent overlapping executions
        )
        
        # Schedule retry of failed reminders every 15 minutes
        self.scheduler.add_job(
            self.retry_failed_reminders,
            trigger=IntervalTrigger(minutes=15),
            id="retry_failed_reminders",
            name="Retry Failed Reminders",
            replace_existing=True,
            max_instances=1
        )
        
        # Schedule snoozed reminders check every 30 seconds
        self.scheduler.add_job(
            self.process_snoozed_reminders,
            trigger=IntervalTrigger(seconds=30),
            id="process_snoozed_reminders",
            name="Process Snoozed Reminders",
            replace_existing=True,
            max_instances=1
        )
        
        # Schedule cleanup of old reminders daily at 2 AM
        self.scheduler.add_job(
            self.cleanup_old_reminders,
            trigger=CronTrigger(hour=2, minute=0),
            id="cleanup_old_reminders",
            name="Cleanup Old Reminders",
            replace_existing=True,
            max_instances=1
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Reminder worker started successfully")
    
    async def stop(self):
        """Stop the reminder worker"""
        if not self.is_running:
            logger.warning("Reminder worker is not running")
            return
            
        logger.info("Stopping reminder worker...")
        
        # Shutdown the scheduler
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        
        logger.info("Reminder worker stopped")
    
    async def process_pending_reminders(self):
        """Process all pending reminders that are due"""
        try:
            db = next(self.db_session_factory())
            reminder_service = ReminderService(db)
            
            # Get pending reminders
            pending_reminders = reminder_service.get_pending_reminders(limit=50)
            
            if not pending_reminders:
                return
                
            logger.info(f"Processing {len(pending_reminders)} pending reminders")
            
            success_count = 0
            failure_count = 0
            
            for reminder in pending_reminders:
                try:
                    success = await reminder_service.send_reminder(reminder)
                    if success:
                        success_count += 1
                        logger.debug(f"Successfully sent reminder {reminder.id}")
                    else:
                        failure_count += 1
                        logger.warning(f"Failed to send reminder {reminder.id}")
                        
                except Exception as e:
                    failure_count += 1
                    logger.error(f"Error processing reminder {reminder.id}: {e}")
                    
            logger.info(f"Processed reminders: {success_count} sent, {failure_count} failed")
            
        except Exception as e:
            logger.error(f"Error in process_pending_reminders: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def retry_failed_reminders(self):
        """Retry failed reminders that haven't exceeded max retry count"""
        try:
            db = next(self.db_session_factory())
            reminder_repo = ReminderRepository(db)
            reminder_service = ReminderService(db)
            
            # Get failed reminders that can be retried
            failed_reminders = reminder_repo.get_failed_reminders(max_retries=3)
            
            if not failed_reminders:
                return
                
            logger.info(f"Retrying {len(failed_reminders)} failed reminders")
            
            retry_success_count = 0
            
            for reminder in failed_reminders:
                try:
                    # Reset to pending status for retry
                    reminder_repo.update(reminder.id, {
                        "status": ReminderStatus.PENDING
                    })
                    
                    success = await reminder_service.send_reminder(reminder)
                    if success:
                        retry_success_count += 1
                        logger.debug(f"Successfully retried reminder {reminder.id}")
                    else:
                        logger.warning(f"Retry failed for reminder {reminder.id}")
                        
                except Exception as e:
                    logger.error(f"Error retrying reminder {reminder.id}: {e}")
                    
            logger.info(f"Retry results: {retry_success_count} successful")
            
        except Exception as e:
            logger.error(f"Error in retry_failed_reminders: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def process_snoozed_reminders(self):
        """Process snoozed reminders that are ready to be sent"""
        try:
            db = next(self.db_session_factory())
            reminder_repo = ReminderRepository(db)
            reminder_service = ReminderService(db)
            
            # Get snoozed reminders that are ready
            ready_reminders = reminder_repo.get_snoozed_reminders_ready()
            
            if not ready_reminders:
                return
                
            logger.info(f"Processing {len(ready_reminders)} snoozed reminders")
            
            for reminder in ready_reminders:
                try:
                    # Reset to pending status
                    reminder_repo.update(reminder.id, {
                        "status": ReminderStatus.PENDING,
                        "snooze_until": None
                    })
                    
                    success = await reminder_service.send_reminder(reminder)
                    if success:
                        logger.debug(f"Successfully sent snoozed reminder {reminder.id}")
                    else:
                        logger.warning(f"Failed to send snoozed reminder {reminder.id}")
                        
                except Exception as e:
                    logger.error(f"Error processing snoozed reminder {reminder.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in process_snoozed_reminders: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def cleanup_old_reminders(self):
        """Clean up old reminders to prevent database bloat"""
        try:
            db = next(self.db_session_factory())
            reminder_repo = ReminderRepository(db)
            
            # Clean up reminders older than 30 days
            deleted_count = reminder_repo.cleanup_old_reminders(days_old=30)
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old reminders")
            else:
                logger.debug("No old reminders to clean up")
                
        except Exception as e:
            logger.error(f"Error in cleanup_old_reminders: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    def get_scheduler_status(self) -> dict:
        """Get status information about the scheduler"""
        jobs = []
        
        if self.scheduler and self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
        
        return {
            "is_running": self.is_running,
            "jobs": jobs,
            "job_count": len(jobs)
        }
    
    async def send_test_reminder(self, reminder_id: str) -> bool:
        """Send a specific reminder immediately (for testing)"""
        try:
            db = next(self.db_session_factory())
            reminder_repo = ReminderRepository(db)
            reminder_service = ReminderService(db)
            
            reminder = reminder_repo.get(reminder_id)
            if not reminder:
                logger.error(f"Reminder {reminder_id} not found")
                return False
                
            success = await reminder_service.send_reminder(reminder)
            
            if success:
                logger.info(f"Test reminder {reminder_id} sent successfully")
            else:
                logger.error(f"Failed to send test reminder {reminder_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending test reminder {reminder_id}: {e}")
            return False
        finally:
            if 'db' in locals():
                db.close()

# Global instance
_reminder_worker: Optional[ReminderWorker] = None

def get_reminder_worker() -> Optional[ReminderWorker]:
    """Get the global reminder worker instance"""
    return _reminder_worker

def initialize_reminder_worker(db_session_factory: sessionmaker) -> ReminderWorker:
    """Initialize the global reminder worker"""
    global _reminder_worker
    _reminder_worker = ReminderWorker(db_session_factory)
    return _reminder_worker