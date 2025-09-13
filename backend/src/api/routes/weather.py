"""
Weather API routes
NO EMOJIS
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, timedelta
import asyncio

from ...services.weather_service import get_weather_service
from ...schemas.weather_schemas import WeatherResponse, ForecastResponse, WeatherTaskSuggestionResponse, WeatherForecastDetail
from ...data.repositories.weather_repo import WeatherRepository
from ..dependencies import get_db

router = APIRouter(tags=["weather"])

@router.get("/current", response_model=WeatherForecastDetail)
async def get_current_weather(
    location: Optional[str] = Query(None, description="Location (default: configured location)"),
    db: Session = Depends(get_db)
):
    """Get current weather conditions with caching"""
    weather_service = get_weather_service()
    
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not available")
    
    try:
        # Get weather with database caching
        forecast = await weather_service.get_current_weather_with_cache(db, location)
        
        if not forecast:
            raise HTTPException(status_code=404, detail="Weather data not found for location")
        
        return WeatherForecastDetail(
            id=forecast.id,
            forecast_date=forecast.forecast_date.isoformat(),
            location=forecast.location,
            temp_high=forecast.temp_high,
            temp_low=forecast.temp_low,
            temp_current=forecast.temp_current,
            feels_like=forecast.feels_like,
            humidity=forecast.humidity,
            weather_condition=forecast.weather_condition,
            weather_description=forecast.weather_description,
            wind_speed_mph=forecast.wind_speed_mph,
            wind_direction=forecast.wind_direction,
            precipitation_probability=forecast.precipitation_probability,
            is_good_outdoor_weather=forecast.is_suitable_for_outdoor_work(),
            comfort_level=forecast.get_comfort_level(),
            data_source=forecast.data_source,
            last_updated=forecast.last_updated.isoformat() if forecast.last_updated else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")

@router.get("/forecast", response_model=List[WeatherForecastDetail])
async def get_weather_forecast(
    location: Optional[str] = Query(None, description="Location (default: configured location)"),
    days: int = Query(5, ge=1, le=7, description="Number of days to forecast"),
    db: Session = Depends(get_db)
):
    """Get weather forecast from database (cached) or fetch new"""
    repo = WeatherRepository(db)
    
    # Get forecasts from database
    forecasts = repo.get_upcoming_days(days, location)
    
    # Check if we need to update
    if not forecasts or len(forecasts) < days:
        weather_service = get_weather_service()
        if weather_service:
            # Update forecast from API
            saved_count = await weather_service.update_forecast_from_api(db, location, days)
            if saved_count > 0:
                # Re-fetch from database
                forecasts = repo.get_upcoming_days(days, location)
    
    return [
        WeatherForecastDetail(
            id=f.id,
            forecast_date=f.forecast_date.isoformat(),
            location=f.location,
            temp_high=f.temp_high,
            temp_low=f.temp_low,
            temp_current=f.temp_current,
            feels_like=f.feels_like,
            humidity=f.humidity,
            weather_condition=f.weather_condition,
            weather_description=f.weather_description,
            wind_speed_mph=f.wind_speed_mph,
            wind_direction=f.wind_direction,
            precipitation_probability=f.precipitation_probability,
            is_good_outdoor_weather=f.is_suitable_for_outdoor_work(),
            comfort_level=f.get_comfort_level(),
            data_source=f.data_source,
            last_updated=f.last_updated.isoformat() if f.last_updated else None
        )
        for f in forecasts
    ]

@router.get("/task-suggestions", response_model=WeatherTaskSuggestionResponse)
async def get_weather_task_suggestions(
    location: Optional[str] = Query(None, description="Location (default: configured location)")
):
    """Get task suggestions based on current weather"""
    weather_service = get_weather_service()
    
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not available - API key not configured")
    
    try:
        condition = await weather_service.get_current_weather(location)
        
        if not condition:
            raise HTTPException(status_code=404, detail="Weather data not found for location")
        
        # Determine recommended task types
        if weather_service.is_good_outdoor_weather(condition):
            recommended_tasks = ["outdoor", "yard_work", "walking", "sports", "gardening"]
            avoid_tasks = []
            suggestion = "Great weather for outdoor activities!"
        else:
            recommended_tasks = ["indoor", "cleaning", "organizing", "reading", "computer_work"]
            avoid_tasks = ["outdoor", "yard_work", "sports", "gardening"]
            suggestion = f"Perfect weather for indoor tasks - {condition.description.lower()}"
        
        return WeatherTaskSuggestionResponse(
            weather_description=weather_service.get_weather_description(condition),
            is_good_outdoor_weather=weather_service.is_good_outdoor_weather(condition),
            recommended_task_types=recommended_tasks,
            avoid_task_types=avoid_tasks,
            suggestion=suggestion,
            temperature=condition.temperature,
            main_condition=condition.main
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating task suggestions: {str(e)}")

@router.get("/suitable-days", response_model=List[WeatherForecastDetail])
async def get_suitable_days(
    activity: str = Query("outdoor_work", description="Activity type: outdoor_work, indoor_work, any_weather"),
    days_ahead: int = Query(7, ge=1, le=14, description="Days to look ahead"),
    location: Optional[str] = Query(None, description="Location (default: configured location)"),
    db: Session = Depends(get_db)
):
    """Get days suitable for specific activities based on weather conditions"""
    repo = WeatherRepository(db)
    
    # Ensure we have forecast data
    weather_service = get_weather_service()
    if weather_service:
        await weather_service.update_forecast_from_api(db, location, days_ahead)
    
    # Get suitable days based on activity
    if activity == "outdoor_work":
        forecasts = repo.get_suitable_days_for_outdoor_work(days_ahead, location)
    elif activity == "indoor_work":
        all_forecasts = repo.get_upcoming_days(days_ahead, location)
        forecasts = [f for f in all_forecasts if f.is_suitable_for_indoor_preference()]
    else:
        forecasts = repo.get_upcoming_days(days_ahead, location)
    
    return [
        WeatherForecastDetail(
            id=f.id,
            forecast_date=f.forecast_date.isoformat(),
            location=f.location,
            temp_high=f.temp_high,
            temp_low=f.temp_low,
            temp_current=f.temp_current,
            feels_like=f.feels_like,
            humidity=f.humidity,
            weather_condition=f.weather_condition,
            weather_description=f.weather_description,
            wind_speed_mph=f.wind_speed_mph,
            wind_direction=f.wind_direction,
            precipitation_probability=f.precipitation_probability,
            is_good_outdoor_weather=f.is_suitable_for_outdoor_work(),
            comfort_level=f.get_comfort_level(),
            data_source=f.data_source,
            last_updated=f.last_updated.isoformat() if f.last_updated else None
        )
        for f in forecasts
    ]

@router.post("/update")
async def update_weather_data(
    location: Optional[str] = Query(None, description="Location (default: configured location)"),
    days: int = Query(7, ge=1, le=14, description="Days to forecast"),
    db: Session = Depends(get_db)
):
    """Manually refresh weather data from API"""
    weather_service = get_weather_service()
    
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not available")
    
    try:
        saved_count = await weather_service.update_forecast_from_api(db, location, days)
        
        return {
            "message": f"Weather data updated successfully",
            "forecasts_saved": saved_count,
            "location": location or weather_service.default_location
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating weather data: {str(e)}")