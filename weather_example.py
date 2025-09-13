"""SQLAlchemy Weather Forecast models"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
import uuid
import requests
import json

from database.sqlalchemy_base import Base

class WeatherForecast(Base):
    """Weather forecast model using SQLAlchemy ORM"""
    __tablename__ = 'weather_forecasts'
    __table_args__ = {'extend_existing': True}
    
    # Primary key and timestamps
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Date this forecast is for
    forecast_date = Column(Date, nullable=False)
    
    # Location info
    location = Column(String, default="Your Location")
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Temperature data (Fahrenheit)
    temp_high = Column(Float)  # Daily high temperature
    temp_low = Column(Float)   # Daily low temperature
    temp_current = Column(Float)  # Current temperature (if available)
    
    # Precipitation data
    precipitation_mm = Column(Float, default=0.0)  # Total precipitation in mm
    precipitation_inches = Column(Float, default=0.0)  # Total precipitation in inches
    precipitation_probability = Column(Integer, default=0)  # Chance of precipitation (0-100%)
    
    # Weather conditions
    weather_condition = Column(String)  # sunny, cloudy, rainy, snow, etc.
    weather_description = Column(String)  # More detailed description
    
    # Wind data
    wind_speed_mph = Column(Float)
    wind_direction = Column(String)  # N, NE, E, SE, S, SW, W, NW
    
    # Other conditions
    humidity = Column(Integer)  # Humidity percentage (0-100)
    visibility_miles = Column(Float)  # Visibility in miles
    uv_index = Column(Integer)  # UV index (0-11+)
    
    # Data source and quality
    data_source = Column(String, default="api")  # api, manual, estimated
    confidence = Column(Integer, default=80)  # Confidence in forecast accuracy (0-100)
    
    def __init__(self, **kwargs):
        super().__init__()
        self.forecast_date = kwargs.get('forecast_date', date.today())
        self.location = kwargs.get('location', "Your Location")
        self.latitude = kwargs.get('latitude')
        self.longitude = kwargs.get('longitude')
        self.temp_high = kwargs.get('temp_high')
        self.temp_low = kwargs.get('temp_low')
        self.temp_current = kwargs.get('temp_current')
        self.precipitation_mm = kwargs.get('precipitation_mm', 0.0)
        self.precipitation_inches = kwargs.get('precipitation_inches', 0.0)
        self.precipitation_probability = kwargs.get('precipitation_probability', 0)
        self.weather_condition = kwargs.get('weather_condition')
        self.weather_description = kwargs.get('weather_description')
        self.wind_speed_mph = kwargs.get('wind_speed_mph')
        self.wind_direction = kwargs.get('wind_direction')
        self.humidity = kwargs.get('humidity')
        self.visibility_miles = kwargs.get('visibility_miles')
        self.uv_index = kwargs.get('uv_index')
        self.data_source = kwargs.get('data_source', 'api')
        self.confidence = kwargs.get('confidence', 80)
    
    def is_suitable_for_outdoor_work(self, min_temp: float = 65.0, max_precipitation_chance: int = 30) -> bool:
        """Check if weather is suitable for outdoor work"""
        if not self.temp_high or not self.precipitation_probability:
            return False  # Can't determine without data
        
        temp_ok = self.temp_high >= min_temp
        precip_ok = self.precipitation_probability <= max_precipitation_chance
        
        return temp_ok and precip_ok
    
    def is_suitable_for_beekeeping(self) -> bool:
        """Check if weather is suitable for beekeeping activities"""
        # Beekeeping requirements:
        # - Temperature above 65°F
        # - Low chance of rain (< 30%)
        # - Not too windy (< 15 mph)
        # - Good visibility
        
        if not all([self.temp_high, self.precipitation_probability]):
            return False
        
        temp_ok = self.temp_high >= 65.0
        rain_ok = self.precipitation_probability < 30
        wind_ok = not self.wind_speed_mph or self.wind_speed_mph < 15.0
        
        return temp_ok and rain_ok and wind_ok
    
    def get_comfort_level(self) -> str:
        """Get general comfort level for outdoor activities"""
        if not self.temp_high:
            return "unknown"
        
        if self.temp_high < 32:
            return "very_cold"
        elif self.temp_high < 50:
            return "cold"
        elif self.temp_high < 65:
            return "cool"
        elif self.temp_high < 75:
            return "comfortable"
        elif self.temp_high < 85:
            return "warm"
        elif self.temp_high < 95:
            return "hot"
        else:
            return "very_hot"
    
    def to_dict(self, include_suitability: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        data = {
            'id': self.id,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'forecast_date': self.forecast_date.isoformat() if self.forecast_date else None,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'temp_high': self.temp_high,
            'temp_low': self.temp_low,
            'temp_current': self.temp_current,
            'precipitation_mm': self.precipitation_mm,
            'precipitation_inches': self.precipitation_inches,
            'precipitation_probability': self.precipitation_probability,
            'weather_condition': self.weather_condition,
            'weather_description': self.weather_description,
            'wind_speed_mph': self.wind_speed_mph,
            'wind_direction': self.wind_direction,
            'humidity': self.humidity,
            'visibility_miles': self.visibility_miles,
            'uv_index': self.uv_index,
            'data_source': self.data_source,
            'confidence': self.confidence
        }
        
        if include_suitability:
            data.update({
                'comfort_level': self.get_comfort_level(),
                'suitable_for_outdoor_work': self.is_suitable_for_outdoor_work(),
                'suitable_for_beekeeping': self.is_suitable_for_beekeeping()
            })
        
        return data
    
    @classmethod
    def get_by_date(cls, session: Session, forecast_date: date) -> Optional['WeatherForecast']:
        """Get weather forecast for a specific date"""
        return session.query(cls).filter(cls.forecast_date == forecast_date).first()
    
    @classmethod
    def get_for_date_range(cls, session: Session, start_date: date, end_date: date) -> List['WeatherForecast']:
        """Get weather forecasts for a date range"""
        return session.query(cls).filter(
            cls.forecast_date >= start_date,
            cls.forecast_date <= end_date
        ).order_by(cls.forecast_date).all()
    
    @classmethod
    def get_upcoming_days(cls, session: Session, days: int = 7) -> List['WeatherForecast']:
        """Get weather forecasts for the next N days"""
        start_date = date.today()
        end_date = start_date + timedelta(days=days-1)
        return cls.get_for_date_range(session, start_date, end_date)
    
    @classmethod
    def get_suitable_days_for_condition(cls, session: Session, 
                                      condition_check: str, 
                                      start_date: date = None,
                                      days_ahead: int = 7) -> List['WeatherForecast']:
        """Get days suitable for specific conditions"""
        if start_date is None:
            start_date = date.today()
        
        forecasts = cls.get_upcoming_days(session, days_ahead)
        suitable_days = []
        
        for forecast in forecasts:
            if condition_check == 'outdoor_work' and forecast.is_suitable_for_outdoor_work():
                suitable_days.append(forecast)
            elif condition_check == 'beekeeping' and forecast.is_suitable_for_beekeeping():
                suitable_days.append(forecast)
            elif condition_check == 'no_rain' and forecast.precipitation_probability < 20:
                suitable_days.append(forecast)
        
        return suitable_days
    
    def save(self, session: Session) -> None:
        """Save weather forecast to database"""
        self.updated_date = datetime.now()
        session.add(self)
        session.commit()
        session.refresh(self)
    
    def delete(self, session: Session) -> None:
        """Delete weather forecast from database"""
        session.delete(self)
        session.commit()
    
    def __repr__(self):
        return f"<WeatherForecast(date='{self.forecast_date}', high={self.temp_high}°F, precip={self.precipitation_probability}%)>"


class WeatherAPI:
    """Weather API integration for fetching forecast data"""
    
    def __init__(self):
        # Default location (you can modify these coordinates for your house)
        self.default_latitude = 39.7392  # Example: Columbus, OH
        self.default_longitude = -104.9903  # Example: Denver, CO (modify for your location)
        self.default_location = "Your House"
    
    def fetch_forecast_openweather(self, api_key: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch weather forecast from OpenWeatherMap API
        Get your free API key at: https://openweathermap.org/api
        """
        try:
            # One Call API 3.0 for detailed forecast
            url = f"http://api.openweathermap.org/data/2.5/forecast"
            params = {
                'lat': self.default_latitude,
                'lon': self.default_longitude,
                'appid': api_key,
                'units': 'imperial',  # Fahrenheit
                'cnt': min(40, days * 8)  # Max 40 forecasts (5 days), 8 per day
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Process the forecast data
            forecasts = []
            daily_data = {}
            
            for item in data.get('list', []):
                forecast_date = datetime.fromtimestamp(item['dt']).date()
                
                if forecast_date not in daily_data:
                    daily_data[forecast_date] = {
                        'temps': [],
                        'precipitation': 0,
                        'conditions': [],
                        'wind_speeds': [],
                        'humidity': []
                    }
                
                # Collect temperature data
                daily_data[forecast_date]['temps'].append(item['main']['temp'])
                
                # Collect precipitation data
                rain = item.get('rain', {}).get('3h', 0)
                snow = item.get('snow', {}).get('3h', 0)
                daily_data[forecast_date]['precipitation'] += (rain + snow)
                
                # Collect other data
                daily_data[forecast_date]['conditions'].append(item['weather'][0]['main'])
                daily_data[forecast_date]['wind_speeds'].append(item['wind']['speed'])
                daily_data[forecast_date]['humidity'].append(item['main']['humidity'])
            
            # Convert to daily summaries
            for forecast_date, day_data in daily_data.items():
                forecasts.append({
                    'forecast_date': forecast_date,
                    'temp_high': max(day_data['temps']) if day_data['temps'] else None,
                    'temp_low': min(day_data['temps']) if day_data['temps'] else None,
                    'precipitation_mm': day_data['precipitation'],
                    'precipitation_inches': day_data['precipitation'] * 0.0393701,  # mm to inches
                    'precipitation_probability': 80 if day_data['precipitation'] > 0 else 20,  # Estimate
                    'weather_condition': max(set(day_data['conditions']), key=day_data['conditions'].count) if day_data['conditions'] else 'unknown',
                    'wind_speed_mph': sum(day_data['wind_speeds']) / len(day_data['wind_speeds']) if day_data['wind_speeds'] else None,
                    'humidity': sum(day_data['humidity']) / len(day_data['humidity']) if day_data['humidity'] else None,
                    'data_source': 'openweather_api',
                    'confidence': 85
                })
            
            return forecasts
            
        except Exception as e:
            print(f"Error fetching OpenWeather forecast: {e}")
            return []
    
    def fetch_forecast_nws(self) -> List[Dict[str, Any]]:
        """
        Fetch weather forecast from National Weather Service (free, no API key needed)
        More reliable for US locations
        """
        try:
            # First, get the grid coordinates for your location
            point_url = f"https://api.weather.gov/points/{self.default_latitude},{self.default_longitude}"
            response = requests.get(point_url, timeout=10)
            response.raise_for_status()
            point_data = response.json()
            
            # Get the forecast URL
            forecast_url = point_data['properties']['forecast']
            
            # Fetch the actual forecast
            response = requests.get(forecast_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
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
                    precip_prob = 70
                elif 'chance' in forecast_text and ('rain' in forecast_text or 'shower' in forecast_text):
                    precip_prob = 40
                elif 'storm' in forecast_text:
                    precip_prob = 80
                
                forecasts.append({
                    'forecast_date': forecast_date,
                    'temp_high': temp_high,
                    'temp_low': temp_low,
                    'precipitation_probability': precip_prob,
                    'weather_condition': day_period['shortForecast'],
                    'weather_description': day_period['detailedForecast'],
                    'wind_speed_mph': self._parse_wind_speed(day_period.get('windSpeed', '')),
                    'wind_direction': day_period.get('windDirection', ''),
                    'data_source': 'nws_api',
                    'confidence': 90
                })
                
                i += 2  # Skip to next day (skip night period)
            
            return forecasts
            
        except Exception as e:
            print(f"Error fetching NWS forecast: {e}")
            return []
    
    def _parse_wind_speed(self, wind_speed_str: str) -> Optional[float]:
        """Parse wind speed string like '10 mph' or '5 to 10 mph'"""
        try:
            import re
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
    
    def save_forecasts_to_db(self, session: Session, forecast_data: List[Dict[str, Any]]) -> int:
        """Save weather forecasts to database"""
        saved_count = 0
        
        for data in forecast_data:
            # Check if forecast already exists for this date
            existing = WeatherForecast.get_by_date(session, data['forecast_date'])
            
            if existing:
                # Update existing forecast
                for key, value in data.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                existing.updated_date = datetime.now()
                session.commit()
            else:
                # Create new forecast
                data['location'] = self.default_location
                data['latitude'] = self.default_latitude
                data['longitude'] = self.default_longitude
                forecast = WeatherForecast(**data)
                forecast.save(session)
                saved_count += 1
        
        return saved_count
    
    def update_forecasts(self, session: Session, api_key: str = None, use_nws: bool = True) -> tuple[int, str]:
        """Update weather forecasts from API"""
        try:
            forecast_data = []
            
            if use_nws:
                # Try NWS first (free, no API key needed)
                forecast_data = self.fetch_forecast_nws()
                
            if not forecast_data and api_key:
                # Fallback to OpenWeatherMap if NWS fails
                forecast_data = self.fetch_forecast_openweather(api_key)
            
            if forecast_data:
                saved_count = self.save_forecasts_to_db(session, forecast_data)
                return saved_count, f"Successfully updated {saved_count} weather forecasts"
            else:
                return 0, "No forecast data available"
                
        except Exception as e:
            return 0, f"Error updating forecasts: {str(e)}"


# Global weather API instance
weather_api = WeatherAPI()