"""
Weather forecast repository implementation
NO EMOJIS
"""
from typing import Optional, List
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .base import BaseRepository
from ..models.weather_model import WeatherForecastModel

class WeatherRepository(BaseRepository[WeatherForecastModel]):
    """Repository for Weather Forecast entities"""
    
    def __init__(self, db: Session):
        super().__init__(WeatherForecastModel, db)
    
    def get_by_date(self, forecast_date: date, location: Optional[str] = None) -> Optional[WeatherForecastModel]:
        """Get weather forecast for a specific date and location"""
        query = self.db.query(WeatherForecastModel).filter(
            WeatherForecastModel.forecast_date == forecast_date
        )
        
        if location:
            query = query.filter(WeatherForecastModel.location == location)
            
        return query.first()
    
    def get_for_date_range(self, start_date: date, end_date: date, location: Optional[str] = None) -> List[WeatherForecastModel]:
        """Get weather forecasts for a date range"""
        query = self.db.query(WeatherForecastModel).filter(
            and_(
                WeatherForecastModel.forecast_date >= start_date,
                WeatherForecastModel.forecast_date <= end_date
            )
        )
        
        if location:
            query = query.filter(WeatherForecastModel.location == location)
            
        return query.order_by(WeatherForecastModel.forecast_date).all()
    
    def get_upcoming_days(self, days: int = 7, location: Optional[str] = None) -> List[WeatherForecastModel]:
        """Get weather forecasts for the next N days"""
        start_date = date.today()
        end_date = start_date + timedelta(days=days-1)
        return self.get_for_date_range(start_date, end_date, location)
    
    def get_suitable_days_for_outdoor_work(self, days_ahead: int = 7, location: Optional[str] = None) -> List[WeatherForecastModel]:
        """Get days suitable for outdoor work in the next N days"""
        forecasts = self.get_upcoming_days(days_ahead, location)
        return [f for f in forecasts if f.is_suitable_for_outdoor_work()]
    
    def get_suitable_days_for_weather_condition(self, required_weather: str, days_ahead: int = 7, location: Optional[str] = None) -> List[WeatherForecastModel]:
        """Get days that match a specific weather condition requirement"""
        forecasts = self.get_upcoming_days(days_ahead, location)
        return [f for f in forecasts if f.matches_task_weather_requirement(required_weather)]
    
    def update_or_create(self, forecast_date: date, location: str, data: dict) -> WeatherForecastModel:
        """Update existing forecast or create new one"""
        existing = self.get_by_date(forecast_date, location)
        
        if existing:
            # Update existing forecast
            for key, value in data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.last_updated = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new forecast
            data['forecast_date'] = forecast_date
            data['location'] = location
            return self.create(data)
    
    def delete_old_forecasts(self, days_to_keep: int = 30) -> int:
        """Delete forecasts older than specified days"""
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        old_forecasts = self.db.query(WeatherForecastModel).filter(
            WeatherForecastModel.forecast_date < cutoff_date
        ).all()
        
        count = len(old_forecasts)
        for forecast in old_forecasts:
            self.db.delete(forecast)
        
        self.db.commit()
        return count
    
    def get_latest_update_time(self, location: Optional[str] = None) -> Optional[datetime]:
        """Get the most recent update time for forecasts"""
        query = self.db.query(WeatherForecastModel.last_updated)
        
        if location:
            query = query.filter(WeatherForecastModel.location == location)
            
        result = query.order_by(WeatherForecastModel.last_updated.desc()).first()
        return result[0] if result else None