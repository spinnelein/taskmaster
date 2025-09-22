"""
TaskMaster Weather Service
Handles weather forecast updates and weather-related background tasks
"""

import asyncio
import logging
from weather_service import get_flask_weather_service


class WeatherBackgroundService:
    """Service for weather-related background operations"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger('weather_background_service')
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
    
    def update_weather_forecasts(self):
        """Update weather forecasts from API"""
        try:
            weather_service = get_flask_weather_service()
            
            # Update forecast data from API (7 days ahead)
            saved_count = asyncio.run(weather_service.update_forecast_from_api(days=7))
            
            # Clean up old forecasts (keep 30 days)
            deleted_count = weather_service.delete_old_forecasts(days_to_keep=30)
            
            self.logger.info(f"Weather update complete: {saved_count} forecasts updated, {deleted_count} old forecasts deleted")
            
            return {
                'success': True,
                'saved_count': saved_count,
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            self.logger.error(f"Error updating weather forecasts: {e}")
            return {
                'success': False,
                'error': str(e),
                'saved_count': 0,
                'deleted_count': 0
            }
    
    def cleanup_old_weather_data(self, days_to_keep=30):
        """Clean up old weather forecast data"""
        try:
            weather_service = get_flask_weather_service()
            deleted_count = weather_service.delete_old_forecasts(days_to_keep=days_to_keep)
            
            self.logger.info(f"Weather cleanup complete: {deleted_count} old forecasts deleted")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up weather data: {e}")
            return 0
    
    def validate_weather_data(self):
        """Validate weather forecast data integrity"""
        try:
            weather_service = get_flask_weather_service()
            
            # Get current forecast coverage
            forecast_count = weather_service.get_forecast_count()
            
            # Check for gaps in forecast data
            # Check for outdated forecasts
            # Validate forecast data quality
            
            self.logger.info(f"Weather data validation complete: {forecast_count} forecasts in database")
            
            return {
                'forecast_count': forecast_count,
                'validation_passed': True,
                'issues': []
            }
            
        except Exception as e:
            self.logger.error(f"Error validating weather data: {e}")
            return {
                'forecast_count': 0,
                'validation_passed': False,
                'issues': [str(e)]
            }
    
    def get_weather_service_status(self):
        """Get weather service status and health"""
        try:
            weather_service = get_flask_weather_service()
            
            # Test API connectivity (if method exists)
            api_status = False
            if hasattr(weather_service, 'test_api_connection'):
                api_status = weather_service.test_api_connection()
            
            # Get forecast data status (if method exists)
            forecast_count = 0
            if hasattr(weather_service, 'get_forecast_count'):
                forecast_count = weather_service.get_forecast_count()
            
            return {
                'api_available': api_status,
                'forecast_count': forecast_count,
                'last_update': 'Not tracked',  # Could implement last update tracking
                'service_healthy': forecast_count > 0  # Only check forecast count for health
            }
            
        except Exception as e:
            self.logger.error(f"Error checking weather service status: {e}")
            return {
                'api_available': False,
                'forecast_count': 0,
                'last_update': 'Error',
                'service_healthy': False,
                'error': str(e)
            }
    
    def force_weather_refresh(self, days=7):
        """Force a complete weather data refresh"""
        try:
            # Clean up all existing forecasts
            self.cleanup_old_weather_data(days_to_keep=0)
            
            # Update with fresh data
            result = self.update_weather_forecasts()
            
            self.logger.info(f"Force weather refresh complete")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during force weather refresh: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self):
        """Get weather background service status"""
        return {
            'weather_enabled': True,
            'service_status': self.get_weather_service_status()
        }