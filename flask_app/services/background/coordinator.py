"""
TaskMaster Background Service Coordinator
Main coordination service that orchestrates all background services
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from .notification_service import NotificationService
from .scheduler_service import SchedulerService
from .maintenance_service import MaintenanceService
from .weather_service import WeatherBackgroundService
from .timepool_service import TimePoolService


class BackgroundServiceCoordinator:
    """
    Main coordinator for all TaskMaster background services
    Provides unified interface and coordinates service interactions
    """
    
    def __init__(self, app=None):
        self.app = app
        self.is_running = False
        self._setup_logging()
        
        # Initialize services
        self.notification_service = NotificationService()
        self.scheduler_service = SchedulerService()
        self.maintenance_service = MaintenanceService()
        self.weather_service = WeatherBackgroundService()
        self.timepool_service = TimePoolService()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Initialize all services with app context
        self.notification_service.init_app(app)
        self.scheduler_service.init_app(app)
        self.maintenance_service.init_app(app)
        self.weather_service.init_app(app)
        self.timepool_service.init_app(app)
    
    def _setup_logging(self):
        """Setup logging for coordinator"""
        self.logger = logging.getLogger('background_coordinator')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def start(self):
        """Start all background services"""
        if self.is_running:
            self.logger.warning("Background services already running")
            return
        
        try:
            # Prepare job functions for scheduler
            job_functions = {
                'process_event_notifications': self._process_event_notifications,
                'process_task_reminders': self._process_task_reminders,
                'send_daily_schedule': self._send_daily_schedule,
                'send_upcoming_events': self._send_upcoming_events,
                'regenerate_task_assignments': self._regenerate_task_assignments,
                'send_priority_task_reminder': self._send_priority_task_reminder,
                'cleanup_old_data': self._cleanup_old_data,
                'health_check': self._health_check,
                'generate_time_pools': self._generate_time_pools,
                'update_weather_forecasts': self._update_weather_forecasts
            }
            
            # Start scheduler with job functions
            self.scheduler_service.start(job_functions)
            
            self.is_running = True
            self.logger.info("TaskMaster Background Services started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting background services: {e}")
            raise
    
    def stop(self):
        """Stop all background services"""
        if not self.is_running:
            return
        
        try:
            self.scheduler_service.stop()
            self.is_running = False
            self.logger.info("TaskMaster Background Services stopped")
        except Exception as e:
            self.logger.error(f"Error stopping background services: {e}")
    
    # Wrapper methods for scheduled jobs (with app context)
    def _process_event_notifications(self):
        """Process event notifications with app context"""
        with self.app.app_context():
            self.notification_service.process_event_notifications()
    
    def _process_task_reminders(self):
        """Process task reminders with app context"""
        with self.app.app_context():
            self.notification_service.process_task_reminders()
    
    def _send_daily_schedule(self):
        """Send daily schedule with app context"""
        with self.app.app_context():
            self.notification_service.send_daily_schedule()
    
    def _send_upcoming_events(self):
        """Send upcoming events with app context"""
        with self.app.app_context():
            self.notification_service.send_upcoming_events()
    
    def _send_priority_task_reminder(self):
        """Send priority task reminder with app context"""
        with self.app.app_context():
            self.notification_service.send_priority_task_reminder()
    
    def _cleanup_old_data(self):
        """Cleanup old data with app context"""
        with self.app.app_context():
            self.maintenance_service.cleanup_old_data()
    
    def _health_check(self):
        """Perform health check with app context"""
        with self.app.app_context():
            self.maintenance_service.health_check()
    
    def _generate_time_pools(self):
        """Generate time pools with app context"""
        with self.app.app_context():
            self.timepool_service.generate_time_pools()
    
    def _update_weather_forecasts(self):
        """Update weather forecasts with app context"""
        with self.app.app_context():
            self.weather_service.update_weather_forecasts()
    
    def _regenerate_task_assignments(self):
        """Regenerate task assignments with app context"""
        with self.app.app_context():
            self.timepool_service._regenerate_task_assignments(context="scheduled")
    
    # Public service access methods
    def register_telegram_chat(self, chat_id: int):
        """Register a new Telegram chat ID"""
        self.notification_service.register_telegram_chat(chat_id)
    
    def regenerate_time_pools(self):
        """Public method to trigger time pool regeneration"""
        if self.scheduler_service.is_running:
            # Schedule immediate regeneration
            self.scheduler_service.add_job(
                func=self._generate_time_pools,
                trigger='date',
                run_date=datetime.now() + timedelta(seconds=5),
                job_id=f'manual_pool_regen_{int(time.time())}',
                name='Manual Time Pool Regeneration',
                max_instances=1
            )
            self.logger.info("Scheduled immediate time pool regeneration")
        else:
            self.logger.warning("Cannot regenerate pools - scheduler not running")
    
    def regenerate_all_time_pools(self, max_days_ahead: int = 30):
        """Regenerate all time pools"""
        with self.app.app_context():
            return self.timepool_service.regenerate_all_time_pools(max_days_ahead)
    
    def update_time_pools_for_range(self, start_date, end_date):
        """Update time pools for a specific date range"""
        with self.app.app_context():
            return self.timepool_service.update_time_pools_for_range(start_date, end_date)
    
    def force_weather_refresh(self, days=7):
        """Force a complete weather data refresh"""
        with self.app.app_context():
            return self.weather_service.force_weather_refresh(days)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all background services"""
        status = {
            'coordinator_running': self.is_running,
            'services': {}
        }
        
        try:
            # Get status from each service
            status['services']['scheduler'] = self.scheduler_service.get_status()
            status['services']['notification'] = self.notification_service.get_status()
            status['services']['maintenance'] = self.maintenance_service.get_status()
            status['services']['weather'] = self.weather_service.get_status()
            
            # Get time pool status with app context if available
            if self.app:
                with self.app.app_context():
                    status['services']['timepool'] = self.timepool_service.get_status()
            else:
                status['services']['timepool'] = {'error': 'No app context available'}
            
        except Exception as e:
            self.logger.error(f"Error getting service status: {e}")
            status['error'] = str(e)
        
        return status