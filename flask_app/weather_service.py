# weather_service.py - Flask weather service wrapper
import os
import asyncio
import aiohttp
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import uuid

from models import db, WeatherForecast

logger = logging.getLogger(__name__)

class FlaskWeatherService:
    """Flask wrapper for weather service functionality"""
    
    def __init__(self, api_key: Optional[str] = None, default_location: str = "Seattle,WA,US"):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.default_location = default_location or os.getenv("WEATHER_LOCATION", "Seattle,WA,US")
        self.default_latitude = float(os.getenv("WEATHER_LATITUDE", "47.6062"))
        self.default_longitude = float(os.getenv("WEATHER_LONGITUDE", "-122.3321"))
        self.nws_forecast_url = os.getenv("NWS_FORECAST_URL", "https://api.weather.gov/gridpoints/SEW/124,67/forecast")
        self.openweather_base_url = "https://api.openweathermap.org/data/2.5"
        self.cache_duration_hours = 3
        
        if not self.api_key:
            logger.info("OpenWeather API key not found - will use National Weather Service API")
    
    def get_by_date(self, target_date: date, location: Optional[str] = None) -> Optional[WeatherForecast]:
        """Get weather forecast for a specific date"""
        query = WeatherForecast.query.filter(WeatherForecast.forecast_date == target_date)
        if location:
            query = query.filter(WeatherForecast.location == location)
        return query.first()
    
    def get_for_date_range(self, start_date: date, end_date: date, location: Optional[str] = None) -> List[WeatherForecast]:
        """Get weather forecasts for a date range"""
        query = WeatherForecast.query.filter(
            WeatherForecast.forecast_date >= start_date,
            WeatherForecast.forecast_date <= end_date
        )
        if location:
            query = query.filter(WeatherForecast.location == location)
        return query.order_by(WeatherForecast.forecast_date).all()
    
    def get_upcoming_days(self, days: int = 7, location: Optional[str] = None) -> List[WeatherForecast]:
        """Get weather forecasts for the next N days"""
        start_date = date.today()
        end_date = start_date + timedelta(days=days-1)
        return self.get_for_date_range(start_date, end_date, location)
    
    def get_suitable_days_for_outdoor_work(self, days_ahead: int = 7, location: Optional[str] = None) -> List[WeatherForecast]:
        """Get days suitable for outdoor work in the next N days"""
        forecasts = self.get_upcoming_days(days_ahead, location)
        return [f for f in forecasts if f.is_suitable_for_outdoor_work()]
    
    def update_or_create(self, forecast_date: date, location: str, data: dict) -> WeatherForecast:
        """Update existing forecast or create new one"""
        existing = self.get_by_date(forecast_date, location)
        
        if existing:
            # Update existing forecast
            for key, value in data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.last_updated = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
        else:
            # Create new forecast
            data['id'] = str(uuid.uuid4())
            data['forecast_date'] = forecast_date
            data['location'] = location
            data['created_at'] = datetime.utcnow()
            data['updated_at'] = datetime.utcnow()
            data['last_updated'] = datetime.utcnow()
            existing = WeatherForecast(**data)
            db.session.add(existing)
        
        try:
            db.session.commit()
            return existing
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving weather forecast: {e}")
            raise
    
    async def fetch_forecast_nws(self) -> List[Dict[str, Any]]:
        """Fetch weather forecast from National Weather Service"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(self.nws_forecast_url) as response:
                    if response.status != 200:
                        logger.error(f"NWS forecast API error: {response.status}")
                        return []
                    
                    data = await response.json()
            
            forecasts = []
            periods = data['properties']['periods']
            
            # Group periods into daily forecasts
            i = 0
            while i < len(periods):
                day_period = periods[i]
                night_period = periods[i + 1] if i + 1 < len(periods) else None
                
                # Parse the start time to get date
                start_time = datetime.fromisoformat(day_period['startTime'].replace('Z', '+00:00'))
                forecast_date = start_time.date()
                
                # Extract temperature data
                if day_period['isDaytime']:
                    temp_high = day_period['temperature']
                    temp_low = night_period['temperature'] if night_period and not night_period['isDaytime'] else None
                else:
                    temp_high = night_period['temperature'] if night_period and night_period['isDaytime'] else None
                    temp_low = day_period['temperature']
                
                # Estimate precipitation from forecast text
                forecast_text = day_period['detailedForecast'].lower()
                precip_prob = 0
                if 'rain' in forecast_text or 'shower' in forecast_text:
                    if 'chance' in forecast_text:
                        # Try to extract percentage
                        match = re.search(r'(\d+)\s*percent', forecast_text)
                        if match:
                            precip_prob = int(match.group(1))
                        else:
                            precip_prob = 40
                    else:
                        precip_prob = 70
                elif 'storm' in forecast_text:
                    precip_prob = 80
                elif 'snow' in forecast_text:
                    precip_prob = 60
                
                forecasts.append({
                    'forecast_date': forecast_date,
                    'temp_high': float(temp_high) if temp_high else None,
                    'temp_low': float(temp_low) if temp_low else None,
                    'precipitation_probability': precip_prob,
                    'weather_condition': day_period['shortForecast'],
                    'weather_description': day_period['detailedForecast'],
                    'wind_speed_mph': self._parse_wind_speed(day_period.get('windSpeed', '')),
                    'wind_direction': day_period.get('windDirection', ''),
                    'data_source': 'nws',
                    'confidence': 90,
                    'latitude': self.default_latitude,
                    'longitude': self.default_longitude
                })
                
                i += 2  # Skip to next day (skip night period)
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error fetching NWS forecast: {e}")
            return []
    
    def _parse_wind_speed(self, wind_speed_str: str) -> Optional[float]:
        """Parse wind speed string like '10 mph' or '5 to 10 mph'"""
        try:
            # Extract numbers from strings like "10 mph" or "5 to 15 mph"
            numbers = re.findall(r'\d+', wind_speed_str)
            if numbers:
                # If range, take the average
                if len(numbers) >= 2:
                    return (int(numbers[0]) + int(numbers[-1])) / 2
                else:
                    return float(numbers[0])
        except:
            pass
        return None
    
    async def get_forecast_openweather(self, location: Optional[str] = None, days: int = 5) -> List[Dict[str, Any]]:
        """Get weather forecast from OpenWeatherMap API"""
        if not self.api_key:
            return []
            
        location = location or self.default_location
        
        try:
            url = f"{self.openweather_base_url}/forecast"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "imperial",
                "cnt": min(days * 8, 40)  # 8 forecasts per day (3-hour intervals), max 40
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"OpenWeather API error: {response.status}")
                        return []
                    
                    data = await response.json()
            
            forecasts = []
            for item in data["list"]:
                dt = datetime.fromtimestamp(item["dt"])
                forecast_date = dt.date()
                
                forecasts.append({
                    'forecast_date': forecast_date,
                    'temp_high': item["main"]["temp"],
                    'temp_low': item["main"]["temp"],
                    'feels_like': item["main"]["feels_like"],
                    'humidity': item["main"]["humidity"],
                    'weather_condition': item["weather"][0]["main"],
                    'weather_description': item["weather"][0]["description"],
                    'wind_speed_mph': item["wind"].get("speed", 0),
                    'precipitation_probability': int(item.get("pop", 0.0) * 100),
                    'data_source': 'openweather',
                    'latitude': self.default_latitude,
                    'longitude': self.default_longitude
                })
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error fetching OpenWeather forecast: {e}")
            return []
    
    async def update_forecast_from_api(self, location: Optional[str] = None, days: int = 7) -> int:
        """Update weather forecast from API and save to database"""
        location = location or self.default_location
        saved_count = 0
        
        # Try National Weather Service first (free, US only)
        try:
            nws_forecasts = await self.fetch_forecast_nws()
            if nws_forecasts:
                for forecast_data in nws_forecasts:
                    saved = self.update_or_create(
                        forecast_data['forecast_date'],
                        location,
                        forecast_data
                    )
                    if saved:
                        saved_count += 1
                
                if saved_count > 0:
                    logger.info(f"Updated {saved_count} forecasts from NWS API")
                    return saved_count
        except Exception as e:
            logger.warning(f"NWS API failed, falling back to OpenWeather: {e}")
        
        # Fall back to OpenWeatherMap if NWS fails or no data
        if self.api_key:
            try:
                forecasts = await self.get_forecast_openweather(location, days)
                
                for forecast_data in forecasts:
                    saved = self.update_or_create(
                        forecast_data['forecast_date'], 
                        location, 
                        forecast_data
                    )
                    if saved:
                        saved_count += 1
                
                if saved_count > 0:
                    logger.info(f"Updated {saved_count} forecasts from OpenWeather API")
            except Exception as e:
                logger.error(f"OpenWeather API failed: {e}")
        
        return saved_count
    
    def delete_old_forecasts(self, days_to_keep: int = 30) -> int:
        """Delete forecasts older than specified days"""
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        old_forecasts = WeatherForecast.query.filter(
            WeatherForecast.forecast_date < cutoff_date
        ).all()
        
        count = len(old_forecasts)
        for forecast in old_forecasts:
            db.session.delete(forecast)
        
        try:
            db.session.commit()
            logger.info(f"Deleted {count} old weather forecasts")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting old forecasts: {e}")
            raise
        
        return count

# Global service instance
_flask_weather_service: Optional[FlaskWeatherService] = None

def get_flask_weather_service() -> FlaskWeatherService:
    """Get the global Flask weather service instance"""
    global _flask_weather_service
    if not _flask_weather_service:
        _flask_weather_service = FlaskWeatherService()
    return _flask_weather_service

def initialize_flask_weather_service(api_key: Optional[str] = None, location: str = "Seattle,WA,US") -> FlaskWeatherService:
    """Initialize the global Flask weather service"""
    global _flask_weather_service
    _flask_weather_service = FlaskWeatherService(api_key, location)
    return _flask_weather_service