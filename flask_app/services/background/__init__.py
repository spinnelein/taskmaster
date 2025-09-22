"""
TaskMaster Background Services Package
Provides modular background services for the TaskMaster Flask application
"""

from .coordinator import BackgroundServiceCoordinator
from .notification_service import NotificationService
from .scheduler_service import SchedulerService
from .maintenance_service import MaintenanceService
from .weather_service import WeatherBackgroundService
from .timepool_service import TimePoolService

# Main service instance for application use
background_service = BackgroundServiceCoordinator()

__all__ = [
    'BackgroundServiceCoordinator',
    'NotificationService', 
    'SchedulerService',
    'MaintenanceService',
    'WeatherBackgroundService',
    'TimePoolService',
    'background_service'
]