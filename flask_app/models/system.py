# system.py - System domain models: WeatherForecast, TaskAssignment
from .base import db, BaseModel
from datetime import datetime


class WeatherForecast(BaseModel):
    __tablename__ = 'weather_forecasts'
    
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


class TaskAssignment(BaseModel):
    __tablename__ = 'task_assignments'
    
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
        from .core import Task
        return Task.query.get(self.task_id)
    
    def get_time_pool(self):
        """Get the associated time pool"""
        from .core import TimePool
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
        from .core import TimePool
        return TaskAssignment.query.join(TimePool).filter(
            TimePool.pool_date >= start_date,
            TimePool.pool_date <= end_date
        ).all()