"""
Weather forecast database model
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Date, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, date
from typing import Optional
from .base_model import BaseModel

class WeatherForecastModel(BaseModel):
    """Weather forecast table model"""
    __tablename__ = "weather_forecasts"
    
    # Date this forecast is for
    forecast_date = Column(Date, nullable=False, index=True)
    
    # Location info
    location = Column(String(255), default="Seattle,WA,US")
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Temperature data (Fahrenheit)
    temp_high = Column(Float)  # Daily high temperature
    temp_low = Column(Float)   # Daily low temperature
    temp_current = Column(Float)  # Current temperature (if available)
    feels_like = Column(Float)  # Feels like temperature
    
    # Precipitation data
    precipitation_mm = Column(Float, default=0.0)  # Total precipitation in mm
    precipitation_inches = Column(Float, default=0.0)  # Total precipitation in inches
    precipitation_probability = Column(Integer, default=0)  # Chance of precipitation (0-100%)
    
    # Weather conditions
    weather_condition = Column(String(50))  # Clear, Clouds, Rain, Snow, etc.
    weather_description = Column(String(255))  # More detailed description
    
    # Wind data
    wind_speed_mph = Column(Float)
    wind_direction = Column(String(10))  # N, NE, E, SE, S, SW, W, NW
    
    # Other conditions
    humidity = Column(Integer)  # Humidity percentage (0-100)
    visibility_miles = Column(Float)  # Visibility in miles
    uv_index = Column(Float)  # UV index (0-11+)
    
    # Data source and quality
    data_source = Column(String(50), default="openweather")  # openweather, nws, manual
    confidence = Column(Integer, default=80)  # Confidence in forecast accuracy (0-100)
    last_updated = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<WeatherForecast(date={self.forecast_date}, high={self.temp_high}°F, condition={self.weather_condition})>"
    
    def is_suitable_for_outdoor_work(self, min_temp: float = 50.0, max_temp: float = 90.0, max_precipitation_chance: int = 30) -> bool:
        """Check if weather is suitable for outdoor work"""
        if not self.temp_high:
            return False  # Can't determine without temperature data
        
        temp_ok = min_temp <= self.temp_high <= max_temp
        
        # If precipitation_probability is None, assume 0
        precip_prob = self.precipitation_probability if self.precipitation_probability is not None else 0
        precip_ok = precip_prob <= max_precipitation_chance
        
        # Check for severe conditions
        severe_conditions = ["thunderstorm", "tornado", "hurricane", "blizzard"]
        condition_ok = not any(condition in (self.weather_condition or "").lower() for condition in severe_conditions)
        
        return temp_ok and precip_ok and condition_ok
    
    def is_suitable_for_indoor_preference(self) -> bool:
        """Check if weather encourages indoor activities"""
        # Indoor activities are preferred when:
        # - It's raining/snowing
        # - Temperature is extreme (too hot or too cold)
        # - High wind speeds
        
        if self.weather_condition and self.weather_condition.lower() in ["rain", "snow", "thunderstorm"]:
            return True
            
        if self.temp_high and (self.temp_high < 40 or self.temp_high > 85):
            return True
            
        if self.wind_speed_mph and self.wind_speed_mph > 25:
            return True
            
        return False
    
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
    
    def matches_task_weather_requirement(self, required_weather: str) -> bool:
        """Check if weather matches task's required weather condition"""
        if required_weather == "any":
            return True
            
        weather_main = (self.weather_condition or "").lower()
        
        weather_mapping = {
            "sunny": ["clear"],
            "clear": ["clear"],
            "cloudy": ["clouds"],
            "rainy": ["rain", "drizzle"],
            "snowy": ["snow"],
            "windy": []  # Check wind speed instead
        }
        
        if required_weather == "windy":
            return self.wind_speed_mph and self.wind_speed_mph >= 10
        
        required_lower = required_weather.lower()
        if required_lower in weather_mapping:
            return any(condition in weather_main for condition in weather_mapping[required_lower])
        
        return False