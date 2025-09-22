# core.py - Core domain models: Event, Task, TimePool
from .base import db, BaseModel, JSONFieldMixin
from datetime import datetime


class Event(BaseModel):
    __tablename__ = 'events'
    
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    event_type = db.Column(db.String(20))
    status = db.Column(db.String(20))
    is_blocking = db.Column(db.Boolean, default=True)
    allows_multitasking = db.Column(db.Boolean)
    buffer_before_minutes = db.Column(db.Integer)
    buffer_after_minutes = db.Column(db.Integer)
    priority = db.Column(db.String(20))
    is_moveable = db.Column(db.Boolean)
    min_notice_hours = db.Column(db.Integer)
    is_recurring = db.Column(db.Boolean)
    recurrence_pattern = db.Column(db.Text)
    recurrence_master_id = db.Column(db.String(36))
    is_recurrence_master = db.Column(db.Boolean)
    is_recurrence_exception = db.Column(db.Boolean)
    recurrence_instance_date = db.Column(db.Date)
    recurrence_parent_id = db.Column(db.String(36))
    project_id = db.Column(db.String(36))
    meal_id = db.Column(db.String(36))  # Foreign key to meals table for dinner events
    attendees = db.Column(db.Text)
    required_resources = db.Column(db.Text)
    reminder_minutes_before = db.Column(db.Integer)
    notifications_enabled = db.Column(db.Boolean)
    
    # Additional recurring event columns from backend schema
    recurrence_rrule = db.Column(db.Text)
    recurrence_end = db.Column(db.DateTime)
    timezone = db.Column(db.String(50))
    dtstart = db.Column(db.DateTime)
    dtend = db.Column(db.DateTime)
    
    def to_dict(self):
        # Format timestamps based on event type
        if self.event_type == 'all_day' and self.start_time and self.end_time:
            # For all-day events, return only date part for FullCalendar
            start_str = self.start_time.date().isoformat()
            end_str = self.end_time.date().isoformat()
            all_day = True
        else:
            # For timed events, return full datetime
            start_str = self.start_time.isoformat() if self.start_time else ''
            end_str = self.end_time.isoformat() if self.end_time else ''
            all_day = False
        
        return {
            'id': self.id,
            'title': self.title,
            'start': start_str,
            'end': end_str,
            'allDay': all_day,
            'color': '#007bff' if self.is_recurring else ('#FF6B6B' if self.is_blocking else '#4ECDC4'),
            'description': self.description or '',
            'location': self.location or '',
            'is_blocking': bool(self.is_blocking),
            'is_recurring': bool(self.is_recurring),
            'is_recurrence_master': bool(self.is_recurrence_master),
            'is_recurrence_exception': bool(self.is_recurrence_exception),
            'recurrence_instance_date': self.recurrence_instance_date.isoformat() if self.recurrence_instance_date else None,
            'recurrence_rrule': self.recurrence_rrule,
            'event_type': self.event_type,
            'status': self.status,
            'meal_id': self.meal_id,
            'is_dinner_event': bool(self.meal_id),
            'notifications_enabled': bool(self.notifications_enabled) if self.notifications_enabled is not None else True
        }
    
    def is_master_event(self):
        """Check if this is a master recurring event (should be shown in event lists)"""
        return not self.is_recurrence_exception and not self.recurrence_instance_date
    
    def get_meal(self):
        """Get the associated meal for dinner events"""
        if self.meal_id:
            # Import here to avoid circular import issues
            from .meals import Meal
            meal = db.session.get(Meal, self.meal_id)
            return meal
        return None
    
    def to_dict_with_meal(self):
        """Get event data with embedded meal information"""
        event_dict = self.to_dict()
        meal = self.get_meal()
        if meal:
            event_dict['meal'] = meal.to_dict_with_dishes()
        else:
            event_dict['meal'] = None
        return event_dict
    
    def is_dinner_event(self):
        """Check if this is a dinner event (has associated meal)"""
        return bool(self.meal_id)


class Task(BaseModel):
    __tablename__ = 'tasks'
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)  # minutes
    urgency = db.Column(db.Integer)  # 1-10
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20))
    due_date = db.Column(db.Date)
    due_time = db.Column(db.Time)
    is_completed = db.Column(db.Boolean)  # Note: actual column name
    is_divisible = db.Column(db.Boolean)
    min_chunk_size = db.Column(db.Integer)
    required_weather = db.Column(db.Text)
    required_context = db.Column(db.Text)
    equipment_needed = db.Column(db.Text)
    depends_on_task_ids = db.Column(db.Text)
    blocks_task_ids = db.Column(db.Text)
    initiative_id = db.Column(db.String(36))
    project_id = db.Column(db.String(36))
    phase_id = db.Column(db.String(36))
    meal_id = db.Column(db.String(36))
    queue_position = db.Column(db.Integer)
    auto_scheduled = db.Column(db.Boolean)
    estimated_cost = db.Column(db.Numeric)
    actual_cost = db.Column(db.Numeric)
    is_recurring = db.Column(db.Boolean)
    recurrence_pattern = db.Column(db.Text)
    parent_task_id = db.Column(db.String(36))
    last_completed_at = db.Column(db.DateTime)
    partial_completion_minutes = db.Column(db.Integer)
    remaining_minutes = db.Column(db.Integer)
    is_snoozed = db.Column(db.Boolean)
    snoozed_until = db.Column(db.DateTime)
    recurrence_days = db.Column(db.Integer)  # Days between recurring instances
    
    # YOLO AI Analysis fields (added by yolo.md migration)
    cognitive_load = db.Column(db.String(20), nullable=True)  # low, medium, high
    ai_analysis = db.Column(db.Text, nullable=True)  # JSON storage for Claude analysis
    last_analyzed = db.Column(db.DateTime, nullable=True)  # When last analyzed by AI
    energy_level = db.Column(db.String(20), nullable=True)  # low, medium, high
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'duration': self.duration or 0,
            'urgency': self.urgency or 5,
            'priority': self.priority or 'medium',
            'status': self.status or 'active',
            'completed': self.is_completed or False,  # Map to correct column
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'snoozed_until': self.snoozed_until.isoformat() if self.snoozed_until else None,
            'is_snoozed': bool(self.is_snoozed),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'initiative_id': self.initiative_id,
            'parent_task_id': self.parent_task_id,
            'recurrence_days': self.recurrence_days,
            'is_recurring': bool(self.recurrence_days and self.recurrence_days > 0),
            'required_weather': self.required_weather,
            # YOLO AI Analysis fields
            'cognitive_load': self.cognitive_load,
            'ai_analysis': self.ai_analysis,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
            'energy_level': self.energy_level
        }


class TimePool(BaseModel, JSONFieldMixin):
    __tablename__ = 'time_pools_flask'  # Use different table name to avoid conflicts
    
    pool_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    total_minutes = db.Column(db.Integer, nullable=False)
    allocated_minutes = db.Column(db.Integer, default=0)
    available_minutes = db.Column(db.Integer, nullable=False)
    
    # Pool context and properties
    is_work_time = db.Column(db.Boolean, default=True)
    is_flexible = db.Column(db.Boolean, default=True)
    context_tags = db.Column(db.Text)  # JSON array of context tags
    
    # Weather integration
    weather_forecast_id = db.Column(db.String(36), db.ForeignKey('weather_forecasts.id'))
    
    def to_dict(self):
        result = {
            'id': self.id,
            'pool_date': self.pool_date.isoformat() if self.pool_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_minutes': self.total_minutes,
            'allocated_minutes': self.allocated_minutes,
            'available_minutes': self.available_minutes,
            'is_work_time': bool(self.is_work_time),
            'is_flexible': bool(self.is_flexible),
            'context_tags': self.context_tags,
            'weather_forecast_id': self.weather_forecast_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Include weather data if available
        weather = self.get_weather_forecast()
        if weather:
            result['weather'] = {
                'temp_high': weather.temp_high,
                'temp_low': weather.temp_low,
                'weather_condition': weather.weather_condition,
                'weather_description': weather.weather_description,
                'precipitation_probability': weather.precipitation_probability,
                'is_suitable_for_outdoor_work': weather.is_suitable_for_outdoor_work(),
                'comfort_level': weather.get_comfort_level(),
                'recommendation': weather.get_recommendation_text()
            }
        
        return result
    
    def get_context_tags_list(self):
        """Get context tags as a list"""
        return self.parse_json_field(self.context_tags)
    
    def set_context_tags_list(self, tags_list):
        """Set context tags from a list"""
        self.context_tags = self.set_json_field(tags_list)
    
    def calculate_available_minutes(self):
        """Calculate and update available minutes"""
        self.available_minutes = max(0, self.total_minutes - (self.allocated_minutes or 0))
        return self.available_minutes
    
    def can_accommodate_duration(self, duration_minutes):
        """Check if pool can accommodate a task of given duration"""
        return self.available_minutes >= duration_minutes
    
    def allocate_time(self, duration_minutes):
        """Allocate time in this pool"""
        if self.can_accommodate_duration(duration_minutes):
            self.allocated_minutes = (self.allocated_minutes or 0) + duration_minutes
            self.calculate_available_minutes()
            return True
        return False
    
    @staticmethod
    def get_pools_for_date_range(start_date, end_date):
        """Get all time pools within a date range"""
        return TimePool.query.filter(
            TimePool.pool_date >= start_date,
            TimePool.pool_date <= end_date
        ).order_by(TimePool.start_time).all()
    
    @staticmethod
    def get_available_pools(start_date, end_date, min_duration_minutes=30):
        """Get pools with available time for tasks"""
        return TimePool.query.filter(
            TimePool.pool_date >= start_date,
            TimePool.pool_date <= end_date,
            TimePool.available_minutes >= min_duration_minutes
        ).order_by(TimePool.start_time).all()
    
    def get_weather_forecast(self):
        """Get the weather forecast for this time pool"""
        if self.weather_forecast_id:
            from .system import WeatherForecast
            return WeatherForecast.query.get(self.weather_forecast_id)
        from .system import WeatherForecast
        return WeatherForecast.get_by_date(self.pool_date)
    
    def is_good_for_outdoor_tasks(self):
        """Check if this time pool is suitable for outdoor tasks"""
        weather = self.get_weather_forecast()
        if weather:
            return weather.is_suitable_for_outdoor_work()
        return None  # Unknown weather
    
    def get_weather_recommendation(self):
        """Get weather-based recommendation for this time pool"""
        weather = self.get_weather_forecast()
        if weather:
            return weather.get_recommendation_text()
        return "Weather data not available"
    
    @staticmethod
    def get_pools_for_outdoor_work(start_date, end_date, min_duration_minutes=30):
        """Get time pools suitable for outdoor work based on weather"""
        pools = TimePool.get_available_pools(start_date, end_date, min_duration_minutes)
        return [pool for pool in pools if pool.is_good_for_outdoor_tasks()]
    
    @staticmethod
    def get_pools_for_indoor_work(start_date, end_date, min_duration_minutes=30):
        """Get time pools suitable for indoor work based on weather"""
        pools = TimePool.get_available_pools(start_date, end_date, min_duration_minutes)
        return [pool for pool in pools if not pool.is_good_for_outdoor_tasks()]