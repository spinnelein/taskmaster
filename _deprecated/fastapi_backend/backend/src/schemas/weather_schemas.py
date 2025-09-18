"""
Weather schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WeatherResponse(BaseModel):
    """Schema for current weather response"""
    temperature: float = Field(..., description="Temperature in Fahrenheit")
    feels_like: float = Field(..., description="Feels like temperature in Fahrenheit")
    humidity: int = Field(..., description="Humidity percentage")
    description: str = Field(..., description="Weather description")
    main: str = Field(..., description="Main weather condition")
    wind_speed: float = Field(..., description="Wind speed in mph")
    visibility: Optional[int] = Field(None, description="Visibility in meters")
    is_good_outdoor_weather: bool = Field(..., description="Whether conditions are good for outdoor activities")
    weather_description: str = Field(..., description="Human-readable weather description")

class ForecastItem(BaseModel):
    """Schema for individual forecast item"""
    datetime: str = Field(..., description="ISO datetime string")
    temperature: float = Field(..., description="Temperature in Fahrenheit")
    feels_like: float = Field(..., description="Feels like temperature in Fahrenheit")
    description: str = Field(..., description="Weather description")
    main: str = Field(..., description="Main weather condition")
    precipitation_probability: float = Field(..., description="Probability of precipitation (0.0-1.0)")
    is_good_outdoor_weather: bool = Field(..., description="Whether conditions are good for outdoor activities")

class ForecastResponse(BaseModel):
    """Schema for weather forecast response"""
    forecasts: List[ForecastItem] = Field(..., description="List of forecast items")

class WeatherTaskSuggestionResponse(BaseModel):
    """Schema for weather-based task suggestions"""
    weather_description: str = Field(..., description="Current weather description")
    is_good_outdoor_weather: bool = Field(..., description="Whether conditions are good for outdoor activities")
    recommended_task_types: List[str] = Field(..., description="Recommended task types for current weather")
    avoid_task_types: List[str] = Field(..., description="Task types to avoid in current weather")
    suggestion: str = Field(..., description="Human-readable suggestion")
    temperature: float = Field(..., description="Current temperature")
    main_condition: str = Field(..., description="Main weather condition")

class WeatherForecastDetail(BaseModel):
    """Detailed weather forecast from database"""
    id: str = Field(..., description="Forecast ID")
    forecast_date: str = Field(..., description="Date of forecast (ISO format)")
    location: str = Field(..., description="Location name")
    temp_high: Optional[float] = Field(None, description="High temperature")
    temp_low: Optional[float] = Field(None, description="Low temperature")
    temp_current: Optional[float] = Field(None, description="Current temperature")
    feels_like: Optional[float] = Field(None, description="Feels like temperature")
    humidity: Optional[int] = Field(None, description="Humidity percentage")
    weather_condition: Optional[str] = Field(None, description="Weather condition")
    weather_description: Optional[str] = Field(None, description="Detailed weather description")
    wind_speed_mph: Optional[float] = Field(None, description="Wind speed in mph")
    wind_direction: Optional[str] = Field(None, description="Wind direction")
    precipitation_probability: Optional[int] = Field(None, description="Precipitation probability percentage")
    is_good_outdoor_weather: bool = Field(..., description="Suitable for outdoor work")
    comfort_level: str = Field(..., description="Comfort level for outdoor activities")
    data_source: Optional[str] = Field(None, description="Data source (openweather, nws, manual)")
    last_updated: Optional[str] = Field(None, description="Last update time (ISO format)")