"""
Weather Service for TaskMaster
NO EMOJIS
"""
import os
import asyncio
import aiohttp
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session

from ..data.repositories.weather_repo import WeatherRepository
from ..data.models.weather_model import WeatherForecastModel

logger = logging.getLogger(__name__)

@dataclass
class WeatherCondition:
    """Weather condition data"""
    temperature: float
    feels_like: float
    humidity: int
    description: str
    main: str  # Rain, Snow, Clear, Clouds, etc.
    wind_speed: float
    visibility: Optional[int] = None
    uv_index: Optional[float] = None

@dataclass
class WeatherForecast:
    """Weather forecast data"""
    datetime: datetime
    condition: WeatherCondition
    pop: float  # Probability of precipitation (0.0-1.0)

class WeatherService:
    """Service for weather data integration"""
    
    def __init__(self, api_key: Optional[str] = None, default_location: str = "Sandy,OR,US"):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.default_location = default_location or os.getenv("WEATHER_LOCATION", "Sandy,OR,US")
        self.default_latitude = float(os.getenv("WEATHER_LATITUDE", "45.3959"))
        self.default_longitude = float(os.getenv("WEATHER_LONGITUDE", "-122.2621"))
        self.nws_forecast_url = os.getenv("NWS_FORECAST_URL", "https://api.weather.gov/gridpoints/PQR/131,93/forecast")
        self.openweather_base_url = "https://api.openweathermap.org/data/2.5"
        self.cache_duration_hours = 3  # Cache weather data for 3 hours
        
        if not self.api_key:
            logger.info("OpenWeather API key not found - will use National Weather Service API")
    
    async def get_current_weather(self, location: Optional[str] = None) -> Optional[WeatherCondition]:
        """Get current weather conditions"""
        if not self.api_key:
            return None
            
        location = location or self.default_location
        
        try:
            url = f"{self.openweather_base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "imperial"  # Fahrenheit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_current_weather(data)
                    else:
                        logger.error(f"Weather API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return None
    
    async def get_forecast(self, location: Optional[str] = None, days: int = 5) -> List[WeatherForecast]:
        """Get weather forecast for next few days"""
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
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_forecast(data)
                    else:
                        logger.error(f"Forecast API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return []
    
    def _parse_current_weather(self, data: Dict[str, Any]) -> WeatherCondition:
        """Parse current weather API response"""
        main = data["main"]
        weather = data["weather"][0]
        wind = data.get("wind", {})
        
        return WeatherCondition(
            temperature=main["temp"],
            feels_like=main["feels_like"],
            humidity=main["humidity"],
            description=weather["description"].title(),
            main=weather["main"],
            wind_speed=wind.get("speed", 0),
            visibility=data.get("visibility")
        )
    
    def _parse_forecast(self, data: Dict[str, Any]) -> List[WeatherForecast]:
        """Parse forecast API response"""
        forecasts = []
        
        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            condition = WeatherCondition(
                temperature=item["main"]["temp"],
                feels_like=item["main"]["feels_like"],
                humidity=item["main"]["humidity"],
                description=item["weather"][0]["description"].title(),
                main=item["weather"][0]["main"],
                wind_speed=item["wind"].get("speed", 0)
            )
            
            forecast = WeatherForecast(
                datetime=dt,
                condition=condition,
                pop=item.get("pop", 0.0)
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def is_good_outdoor_weather(self, condition: WeatherCondition) -> bool:
        """Determine if weather is good for outdoor activities"""
        if condition.main in ["Rain", "Snow", "Thunderstorm"]:
            return False
        
        if condition.temperature < 40 or condition.temperature > 95:
            return False
            
        if condition.wind_speed > 25:  # Too windy
            return False
            
        return True
    
    def is_good_indoor_weather(self, condition: WeatherCondition) -> bool:
        """Determine if weather encourages indoor activities"""
        return not self.is_good_outdoor_weather(condition)
    
    def get_weather_description(self, condition: WeatherCondition) -> str:
        """Get human-readable weather description"""
        temp_desc = ""
        if condition.temperature < 32:
            temp_desc = "freezing"
        elif condition.temperature < 50:
            temp_desc = "cold"
        elif condition.temperature < 70:
            temp_desc = "cool"
        elif condition.temperature < 80:
            temp_desc = "comfortable"
        elif condition.temperature < 90:
            temp_desc = "warm"
        else:
            temp_desc = "hot"
        
        return f"{condition.description}, {int(condition.temperature)}°F ({temp_desc})"
    
    def suggest_task_timing(self, condition: WeatherCondition, is_outdoor_task: bool) -> str:
        """Suggest timing for a task based on weather"""
        if is_outdoor_task:
            if self.is_good_outdoor_weather(condition):
                return "Great weather for this outdoor activity!"
            else:
                return f"Consider postponing - {condition.description.lower()} expected"
        else:
            if self.is_good_indoor_weather(condition):
                return "Perfect weather to focus on indoor tasks"
            else:
                return "Nice weather - maybe save indoor tasks for later?"
    
    async def get_current_weather_with_cache(self, db: Session, location: Optional[str] = None) -> Optional[WeatherForecastModel]:
        """Get current weather with database caching"""
        location = location or self.default_location
        repo = WeatherRepository(db)
        
        # Check cache first
        today = date.today()
        cached = repo.get_by_date(today, location)
        
        if cached and cached.last_updated:
            # Check if cache is still fresh
            cache_age = datetime.now() - cached.last_updated
            if cache_age.total_seconds() < self.cache_duration_hours * 3600:
                return cached
        
        # Fetch fresh data
        current = await self.get_current_weather(location)
        if current:
            # Save to database
            forecast_data = {
                'temp_current': current.temperature,
                'temp_high': current.temperature,  # For current, use same temp
                'temp_low': current.temperature,
                'feels_like': current.feels_like,
                'humidity': current.humidity,
                'weather_condition': current.main,
                'weather_description': current.description,
                'wind_speed_mph': current.wind_speed,
                'visibility_miles': current.visibility / 1609.344 if current.visibility else None,
                'data_source': 'openweather',
                'location': location,
                'latitude': self.default_latitude,
                'longitude': self.default_longitude
            }
            
            return repo.update_or_create(today, location, forecast_data)
        
        return None
    
    async def update_forecast_from_api(self, db: Session, location: Optional[str] = None, days: int = 5) -> int:
        """Update weather forecast from API and save to database"""
        location = location or self.default_location
        repo = WeatherRepository(db)
        saved_count = 0
        
        # Try National Weather Service first (free, US only)
        if self.default_latitude and self.default_longitude:
            try:
                nws_forecasts = await self.fetch_forecast_nws()
                if nws_forecasts:
                    for forecast_data in nws_forecasts:
                        saved = repo.update_or_create(
                            forecast_data['forecast_date'],
                            location,
                            forecast_data
                        )
                        if saved:
                            saved_count += 1
                    
                    if saved_count > 0:
                        return saved_count
            except Exception as e:
                logger.warning(f"NWS API failed, falling back to OpenWeather: {e}")
        
        # Fall back to OpenWeatherMap if NWS fails or no data
        if self.api_key:
            forecasts = await self.get_forecast(location, days)
            
            for forecast in forecasts:
                forecast_date = forecast.datetime.date()
                
                forecast_data = {
                    'temp_high': forecast.condition.temperature,
                    'temp_low': forecast.condition.temperature,
                    'feels_like': forecast.condition.feels_like,
                    'humidity': forecast.condition.humidity,
                    'weather_condition': forecast.condition.main,
                    'weather_description': forecast.condition.description,
                    'wind_speed_mph': forecast.condition.wind_speed,
                    'precipitation_probability': int(forecast.pop * 100),
                    'data_source': 'openweather',
                    'location': location,
                    'latitude': self.default_latitude,
                    'longitude': self.default_longitude
                }
                
                saved = repo.update_or_create(forecast_date, location, forecast_data)
                if saved:
                    saved_count += 1
        
        return saved_count
    
    async def fetch_forecast_nws(self) -> List[Dict[str, Any]]:
        """
        Fetch weather forecast from National Weather Service using direct gridpoint URL
        """
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
                    'confidence': 90
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

# Global service instance
_weather_service: Optional[WeatherService] = None

def get_weather_service() -> Optional[WeatherService]:
    """Get the global weather service instance"""
    return _weather_service

def initialize_weather_service(api_key: Optional[str] = None, location: str = "Seattle,WA,US") -> WeatherService:
    """Initialize the global weather service"""
    global _weather_service
    _weather_service = WeatherService(api_key, location)
    return _weather_service