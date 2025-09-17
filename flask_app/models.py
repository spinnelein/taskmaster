# models.py - Separate models file to avoid circular imports
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# Create db instance that will be initialized by the app
db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.String(36), primary_key=True)
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
    attendees = db.Column(db.Text)
    required_resources = db.Column(db.Text)
    reminder_minutes_before = db.Column(db.Integer)
    notifications_enabled = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    
    # Additional recurring event columns from backend schema
    recurrence_rrule = db.Column(db.Text)
    recurrence_end = db.Column(db.DateTime)
    timezone = db.Column(db.String(50))
    dtstart = db.Column(db.DateTime)
    dtend = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start': self.start_time.isoformat() if self.start_time else '',
            'end': self.end_time.isoformat() if self.end_time else '',
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
            'notifications_enabled': bool(self.notifications_enabled) if self.notifications_enabled is not None else True
        }
    
    def is_master_event(self):
        """Check if this is a master recurring event (should be shown in event lists)"""
        return not self.is_recurrence_exception and not self.recurrence_instance_date

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.String(36), primary_key=True)
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
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    recurrence_days = db.Column(db.Integer)  # Days between recurring instances
    
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
            'is_recurring': bool(self.recurrence_days and self.recurrence_days > 0)
        }

class Initiative(db.Model):
    __tablename__ = 'initiatives'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20))  # ACTIVE, COMPLETED, PAUSED
    is_template = db.Column(db.Boolean, default=False)
    target_completion_count = db.Column(db.Integer)
    current_completion_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    
    # Following plan.md - initiatives should have task_templates JSON field
    # For now, we'll work with existing schema and add task_templates functionality in API layer
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'status': self.status or 'ACTIVE',
            'is_template': bool(self.is_template),
            'target_completion_count': self.target_completion_count or 0,
            'current_completion_count': self.current_completion_count or 0,
            'progress_percentage': self.calculate_progress(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'task_count': self.get_task_count()
        }
    
    def calculate_progress(self):
        """Calculate completion percentage"""
        if not self.target_completion_count or self.target_completion_count == 0:
            return 0
        percentage = (self.current_completion_count / self.target_completion_count) * 100
        return min(100, max(0, round(percentage, 1)))
    
    def get_task_count(self):
        """Get count of tasks associated with this initiative"""
        # In Flask, we'll query tasks separately to avoid relationship issues
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT COUNT(*) FROM tasks WHERE initiative_id = :init_id AND is_completed = 0"),
            {"init_id": self.id}
        ).scalar()
        return result or 0

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(9), nullable=False)  # PLANNING, ACTIVE, COMPLETED
    priority = db.Column(db.String(8), nullable=False)  # LOW, MEDIUM, HIGH
    estimated_start_date = db.Column(db.DateTime)
    estimated_end_date = db.Column(db.DateTime)
    actual_start_date = db.Column(db.DateTime)
    actual_end_date = db.Column(db.DateTime)
    initiative_id = db.Column(db.String(36))
    template_id = db.Column(db.String(36))
    tags = db.Column(db.Text)  # JSON
    custom_fields = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'status': self.status,
            'priority': self.priority,
            'estimated_start_date': self.estimated_start_date.isoformat() if self.estimated_start_date else None,
            'estimated_end_date': self.estimated_end_date.isoformat() if self.estimated_end_date else None,
            'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'initiative_id': self.initiative_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProjectPhase(db.Model):
    __tablename__ = 'project_phases'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(9), nullable=False)  # PLANNING, ACTIVE, COMPLETED
    estimated_start_date = db.Column(db.DateTime)
    estimated_end_date = db.Column(db.DateTime)
    actual_start_date = db.Column(db.DateTime)
    actual_end_date = db.Column(db.DateTime)
    depends_on_phase_ids = db.Column(db.Text)  # JSON
    project_id = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'order': self.order,
            'status': self.status,
            'estimated_start_date': self.estimated_start_date.isoformat() if self.estimated_start_date else None,
            'estimated_end_date': self.estimated_end_date.isoformat() if self.estimated_end_date else None,
            'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
            'actual_end_date': self.actual_end_date.isoformat() if self.actual_end_date else None,
            'depends_on_phase_ids': self.depends_on_phase_ids,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TimePool(db.Model):
    __tablename__ = 'time_pools_flask'  # Use different table name to avoid conflicts
    
    id = db.Column(db.String(36), primary_key=True)
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
    
    # Metadata
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
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
        if not self.context_tags:
            return []
        try:
            import json
            return json.loads(self.context_tags)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_context_tags_list(self, tags_list):
        """Set context tags from a list"""
        import json
        self.context_tags = json.dumps(tags_list) if tags_list else None
    
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
            return WeatherForecast.query.get(self.weather_forecast_id)
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

class WeatherForecast(db.Model):
    __tablename__ = 'weather_forecasts'
    
    id = db.Column(db.String(36), primary_key=True)
    forecast_date = db.Column(db.Date, nullable=False, index=True)
    
    # Location info
    location = db.Column(db.String(255), default="Seattle,WA,US")
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Temperature data (Fahrenheit)
    temp_high = db.Column(db.Float)
    temp_low = db.Column(db.Float)
    temp_current = db.Column(db.Float)
    feels_like = db.Column(db.Float)
    
    # Precipitation data
    precipitation_mm = db.Column(db.Float, default=0.0)
    precipitation_inches = db.Column(db.Float, default=0.0)
    precipitation_probability = db.Column(db.Integer, default=0)
    
    # Weather conditions
    weather_condition = db.Column(db.String(50))
    weather_description = db.Column(db.String(255))
    
    # Wind data
    wind_speed_mph = db.Column(db.Float)
    wind_direction = db.Column(db.String(10))
    
    # Other conditions
    humidity = db.Column(db.Integer)
    visibility_miles = db.Column(db.Float)
    uv_index = db.Column(db.Float)
    
    # Data source and quality
    data_source = db.Column(db.String(50), default="openweather")
    confidence = db.Column(db.Integer, default=80)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Standard timestamps
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'forecast_date': self.forecast_date.isoformat() if self.forecast_date else None,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'temp_high': self.temp_high,
            'temp_low': self.temp_low,
            'temp_current': self.temp_current,
            'feels_like': self.feels_like,
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
            'confidence': self.confidence,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_suitable_for_outdoor_work(self, min_temp=50.0, max_temp=90.0, max_precipitation_chance=30):
        """Check if weather is suitable for outdoor work"""
        if not self.temp_high:
            return False
        
        temp_ok = min_temp <= self.temp_high <= max_temp
        precip_prob = self.precipitation_probability if self.precipitation_probability is not None else 0
        precip_ok = precip_prob <= max_precipitation_chance
        
        severe_conditions = ["thunderstorm", "tornado", "hurricane", "blizzard"]
        condition_ok = not any(condition in (self.weather_condition or "").lower() for condition in severe_conditions)
        
        return temp_ok and precip_ok and condition_ok
    
    def is_suitable_for_indoor_preference(self):
        """Check if weather encourages indoor activities"""
        if self.weather_condition and self.weather_condition.lower() in ["rain", "snow", "thunderstorm"]:
            return True
            
        if self.temp_high and (self.temp_high < 40 or self.temp_high > 85):
            return True
            
        if self.wind_speed_mph and self.wind_speed_mph > 25:
            return True
            
        return False
    
    def get_comfort_level(self):
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
    
    def get_recommendation_text(self):
        """Get human-readable weather recommendation"""
        if self.is_suitable_for_outdoor_work():
            comfort = self.get_comfort_level()
            if comfort == "comfortable":
                return "Perfect weather for outdoor activities!"
            elif comfort in ["cool", "warm"]:
                return "Great weather for outdoor tasks!"
            else:
                return "Good weather for outdoor work"
        else:
            if self.is_suitable_for_indoor_preference():
                if "rain" in (self.weather_condition or "").lower():
                    return "Rainy day - perfect for indoor focus work"
                elif self.temp_high and self.temp_high > 85:
                    return "Hot day - stay cool with indoor tasks"
                elif self.temp_high and self.temp_high < 40:
                    return "Cold day - cozy indoor work time"
                else:
                    return "Weather favors indoor activities"
            else:
                return "Mixed conditions - plan accordingly"
    
    @staticmethod
    def get_by_date(target_date, location=None):
        """Get weather forecast for a specific date"""
        query = WeatherForecast.query.filter(WeatherForecast.forecast_date == target_date)
        if location:
            query = query.filter(WeatherForecast.location == location)
        return query.first()

class TaskAssignment(db.Model):
    __tablename__ = 'task_assignments'
    
    id = db.Column(db.String(36), primary_key=True)
    task_id = db.Column(db.String(36), db.ForeignKey('tasks.id'), nullable=False)
    time_pool_id = db.Column(db.String(36), db.ForeignKey('time_pools_flask.id'), nullable=False)
    
    # Assignment details
    allocated_minutes = db.Column(db.Integer, nullable=False)
    scheduled_start = db.Column(db.DateTime)  # Specific start time within the pool
    scheduled_end = db.Column(db.DateTime)    # Specific end time within the pool
    
    # Status tracking
    status = db.Column(db.String(20), default='assigned')  # assigned, started, completed, cancelled
    is_partial = db.Column(db.Boolean, default=False)      # Is this a partial allocation of a larger task?
    
    # Progress tracking
    actual_start = db.Column(db.DateTime)
    actual_end = db.Column(db.DateTime)
    minutes_worked = db.Column(db.Integer, default=0)
    
    # Assignment metadata
    assigned_at = db.Column(db.DateTime, nullable=False)
    assigned_by = db.Column(db.String(50), default='system')  # 'user' or 'system'
    notes = db.Column(db.Text)
    
    # Standard timestamps
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'time_pool_id': self.time_pool_id,
            'allocated_minutes': self.allocated_minutes,
            'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None,
            'scheduled_end': self.scheduled_end.isoformat() if self.scheduled_end else None,
            'status': self.status,
            'is_partial': bool(self.is_partial),
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'minutes_worked': self.minutes_worked,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'assigned_by': self.assigned_by,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_task(self):
        """Get the associated task"""
        return Task.query.get(self.task_id)
    
    def get_time_pool(self):
        """Get the associated time pool"""
        return TimePool.query.get(self.time_pool_id)
    
    def can_fit_in_pool(self):
        """Check if this assignment can fit in the assigned time pool"""
        pool = self.get_time_pool()
        if not pool:
            return False
        return pool.available_minutes >= self.allocated_minutes
    
    def mark_started(self):
        """Mark the assignment as started"""
        self.status = 'started'
        self.actual_start = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, minutes_worked=None):
        """Mark the assignment as completed"""
        self.status = 'completed'
        self.actual_end = datetime.utcnow()
        if minutes_worked is not None:
            self.minutes_worked = minutes_worked
        self.updated_at = datetime.utcnow()
    
    def cancel_assignment(self, reason=None):
        """Cancel the assignment and free up the time pool"""
        pool = self.get_time_pool()
        if pool:
            # Return allocated minutes to the pool
            pool.allocated_minutes = max(0, pool.allocated_minutes - self.allocated_minutes)
            pool.available_minutes = pool.total_minutes - pool.allocated_minutes
        
        self.status = 'cancelled'
        if reason:
            self.notes = f"{self.notes or ''}\nCancelled: {reason}".strip()
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def get_assignments_for_task(task_id):
        """Get all assignments for a specific task"""
        return TaskAssignment.query.filter_by(task_id=task_id).all()
    
    @staticmethod
    def get_assignments_for_pool(time_pool_id):
        """Get all assignments for a specific time pool"""
        return TaskAssignment.query.filter_by(time_pool_id=time_pool_id).all()
    
    @staticmethod
    def get_active_assignments():
        """Get all active (assigned or started) assignments"""
        return TaskAssignment.query.filter(
            TaskAssignment.status.in_(['assigned', 'started'])
        ).all()
    
    @staticmethod
    def get_assignments_for_date_range(start_date, end_date):
        """Get assignments within a date range"""
        return TaskAssignment.query.join(TimePool).filter(
            TimePool.pool_date >= start_date,
            TimePool.pool_date <= end_date
        ).all()