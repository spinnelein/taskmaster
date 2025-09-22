"""
TaskMaster Time Pool Service
Handles time pool generation and task assignment operations
"""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta, date
from typing import Tuple
from sqlalchemy import and_, or_
from models import db, Event, TimePool, WeatherForecast
from recurring_service import recurring_service
from assignment_service import get_assignment_service


class TimePoolService:
    """Service for time pool generation and management"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger('timepool_service')
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
    
    def generate_time_pools(self):
        """Generate time pools based on scheduled events"""
        try:
            # Define work hours (6 AM to 11 PM for broader coverage)
            work_start_hour = 6
            work_end_hour = 19
            min_pool_duration = 30  # Minimum 30 minutes
            
            # Find date range based on actual events (limited to 30 days ahead)
            earliest_event = db.session.query(Event.start_time).order_by(Event.start_time.asc()).first()
            latest_event = db.session.query(Event.start_time).order_by(Event.start_time.desc()).first()
            
            if not earliest_event or not latest_event:
                self.logger.info("No events found - creating pools for next 30 days")
                start_date = datetime.now().date()
                end_date = start_date + timedelta(days=30)
            else:
                # Include actual event dates but limit future generation to 30 days
                start_date = min(earliest_event[0].date(), datetime.now().date())
                max_future_date = datetime.now().date() + timedelta(days=30)
                end_date = min(max(latest_event[0].date(), datetime.now().date()), max_future_date)
            
            self.logger.info(f"Generating time pools from {start_date} to {end_date}")
            
            # Clean up old pools (older than start_date)
            old_pools = TimePool.query.filter(TimePool.pool_date < start_date).all()
            for pool in old_pools:
                db.session.delete(pool)
            
            pools_created = 0
            pools_updated = 0
            
            # Process each day in the range
            current_date = start_date
            while current_date <= end_date:
                day_pools_created, day_pools_updated = self._generate_pools_for_date(
                    current_date, work_start_hour, work_end_hour, min_pool_duration
                )
                pools_created += day_pools_created
                pools_updated += day_pools_updated
                current_date += timedelta(days=1)
            
            db.session.commit()
            self.logger.info(f"Time pool generation complete: {pools_created} created, {pools_updated} updated")
            
            # Regenerate task assignments after daily pool generation
            self._regenerate_task_assignments(context="daily_generation")
            
            return pools_created, pools_updated
            
        except Exception as e:
            self.logger.error(f"Error generating time pools: {e}")
            db.session.rollback()
            return 0, 0
    
    def _generate_pools_for_date(self, target_date, work_start_hour, work_end_hour, min_pool_duration):
        """Generate time pools for a specific date"""
        pools_created = 0
        pools_updated = 0
        
        # Get only master recurring events for expansion
        master_recurring_events = Event.query.filter(
            Event.is_recurrence_master == True
        ).all()
        
        # Expand recurring events for this specific date
        expanded_events = recurring_service.expand_events_for_period(master_recurring_events, target_date, target_date)
        
        self.logger.info(f"Expanded {len(expanded_events)} events for {target_date}")
        
        # Filter to only blocking events and convert to event-like objects
        blocking_events = []
        for event_dict in expanded_events:
            if event_dict.get('is_blocking', False):
                # Create a simple object with the needed attributes
                class EventInstance:
                    def __init__(self, event_dict):
                        self.start_time = datetime.fromisoformat(event_dict['start'])
                        self.end_time = datetime.fromisoformat(event_dict['end'])
                        self.title = event_dict['title']
                        self.is_blocking = event_dict['is_blocking']
                        self.buffer_before_minutes = 0
                        self.buffer_after_minutes = 0
                
                blocking_events.append(EventInstance(event_dict))
                self.logger.info(f"Added blocking event: {event_dict['title']} at {event_dict['start']}")
        
        # Also get any non-recurring events for this date
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date, datetime.max.time())
        
        non_recurring_events = db.session.query(Event).filter(
            and_(
                Event.start_time >= day_start,
                Event.start_time <= day_end,
                Event.is_blocking == True,
                or_(Event.is_recurring.is_(None), Event.is_recurring == False)
            )
        ).all()
        
        blocking_events.extend(non_recurring_events)
        
        self.logger.info(f"Found {len(blocking_events)} total blocking events for {target_date}")
        
        # Delete existing pools for this date to regenerate
        existing_pools = TimePool.query.filter(TimePool.pool_date == target_date).all()
        for pool in existing_pools:
            db.session.delete(pool)
        
        # If no events, create one large pool for the work day
        if not blocking_events:
            work_day_start = datetime.combine(target_date, datetime.min.time().replace(hour=work_start_hour))
            work_day_end = datetime.combine(target_date, datetime.min.time().replace(hour=work_end_hour))
            work_duration = (work_day_end - work_day_start).total_seconds() / 60
            
            if work_duration >= min_pool_duration:
                pool = self._create_time_pool(target_date, work_day_start, work_day_end, work_duration)
                if pool:
                    pools_created += 1
            return pools_created, pools_updated
        
        # Process events to find gaps
        work_day_start = datetime.combine(target_date, datetime.min.time().replace(hour=work_start_hour))
        work_day_end = datetime.combine(target_date, datetime.min.time().replace(hour=work_end_hour))
        
        # Create list of time slots occupied by events
        occupied_slots = []
        for event in blocking_events:
            start_time = max(event.start_time, work_day_start)  # Don't go before work hours
            end_time = min(event.end_time or event.start_time + timedelta(hours=1), work_day_end)  # Don't go past work hours
            
            # Add buffer time if specified
            buffer_before = getattr(event, 'buffer_before_minutes', 0) or 0
            buffer_after = getattr(event, 'buffer_after_minutes', 0) or 0
            
            buffer_start = start_time - timedelta(minutes=buffer_before)
            buffer_end = end_time + timedelta(minutes=buffer_after)
            
            # Keep within work hours
            buffer_start = max(buffer_start, work_day_start)
            buffer_end = min(buffer_end, work_day_end)
            
            occupied_slots.append((buffer_start, buffer_end))
        
        # Merge overlapping occupied slots
        occupied_slots.sort()
        merged_slots = []
        for start, end in occupied_slots:
            if merged_slots and start <= merged_slots[-1][1]:
                # Overlapping - extend the last slot
                merged_slots[-1] = (merged_slots[-1][0], max(merged_slots[-1][1], end))
            else:
                merged_slots.append((start, end))
        
        # Find gaps between occupied slots and create pools
        current_time = work_day_start
        
        for occupied_start, occupied_end in merged_slots:
            # Create pool before this occupied slot
            if occupied_start > current_time:
                gap_duration = (occupied_start - current_time).total_seconds() / 60
                if gap_duration >= min_pool_duration:
                    pool = self._create_time_pool(target_date, current_time, occupied_start, gap_duration)
                    if pool:
                        pools_created += 1
                        self.logger.debug(f"Created pool: {current_time.strftime('%H:%M')} - {occupied_start.strftime('%H:%M')} ({gap_duration:.0f}min)")
            
            # Move current time to end of this occupied slot
            current_time = occupied_end
        
        # Create final pool if there's time left after the last event
        if current_time < work_day_end:
            final_duration = (work_day_end - current_time).total_seconds() / 60
            if final_duration >= min_pool_duration:
                pool = self._create_time_pool(target_date, current_time, work_day_end, final_duration)
                if pool:
                    pools_created += 1
                    self.logger.debug(f"Created final pool: {current_time.strftime('%H:%M')} - {work_day_end.strftime('%H:%M')} ({final_duration:.0f}min)")
        
        return pools_created, pools_updated
    
    def _create_time_pool(self, pool_date, start_time, end_time, duration_minutes):
        """Create a time pool record"""
        try:
            # Determine context tags based on time period (not just start hour)
            start_hour = start_time.hour
            end_hour = end_time.hour
            duration_hours = (end_time - start_time).total_seconds() / 3600
            context_tags = []
            
            # For pools longer than 4 hours, determine dominant work period
            if duration_hours > 4:
                # Long pool - determine if it's primarily work time
                work_hours_covered = 0
                for h in range(start_hour, end_hour + 1):
                    if 8 <= h <= 20:  # Business hours 8 AM - 8 PM
                        work_hours_covered += 1
                
                if work_hours_covered >= (end_hour - start_hour) * 0.6:  # 60% work time
                    context_tags = ['work_day', 'work_time', 'mixed_periods']
                    is_work_time = True
                else:
                    context_tags = ['mixed_periods', 'personal_time']
                    is_work_time = False
            else:
                # Short pool - use start hour logic
                if 8 <= start_hour < 12:
                    context_tags = ['morning', 'work_time', 'focus_time']
                    is_work_time = True
                elif 12 <= start_hour < 14:
                    context_tags = ['lunch_time', 'break_time']
                    is_work_time = False
                elif 14 <= start_hour < 18:
                    context_tags = ['afternoon', 'work_time', 'meetings']
                    is_work_time = True
                elif 18 <= start_hour < 20:
                    context_tags = ['evening', 'work_time', 'admin_time']
                    is_work_time = True
                elif 20 <= start_hour < 22:
                    context_tags = ['evening', 'personal_time', 'flexible']
                    is_work_time = False
                else:
                    context_tags = ['off_hours', 'personal_time']
                    is_work_time = False
            
            # Get weather forecast for this date
            weather_forecast = WeatherForecast.get_by_date(pool_date)
            weather_forecast_id = weather_forecast.id if weather_forecast else None
            
            # Add weather-based context tags
            if weather_forecast:
                if weather_forecast.is_suitable_for_outdoor_work():
                    context_tags.append('good_weather')
                    context_tags.append('outdoor_suitable')
                else:
                    context_tags.append('indoor_preferred')
                
                comfort_level = weather_forecast.get_comfort_level()
                context_tags.append(f'weather_{comfort_level}')
                
                if weather_forecast.precipitation_probability and weather_forecast.precipitation_probability > 50:
                    context_tags.append('rain_likely')
            
            # Create the time pool
            pool = TimePool(
                id=str(uuid.uuid4()),
                pool_date=pool_date,
                start_time=start_time,
                end_time=end_time,
                total_minutes=int(duration_minutes),
                allocated_minutes=0,
                available_minutes=int(duration_minutes),
                is_work_time=is_work_time,
                is_flexible=True,
                context_tags=json.dumps(context_tags),
                weather_forecast_id=weather_forecast_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(pool)
            return pool
            
        except Exception as e:
            self.logger.error(f"Error creating time pool: {e}")
            return None
    
    def regenerate_time_pools(self):
        """Public method to trigger time pool regeneration"""
        return self.generate_time_pools()
    
    def regenerate_all_time_pools(self, max_days_ahead: int = 30) -> Tuple[int, int]:
        """
        Regenerate time pools for all dates (up to max_days_ahead).
        This method can be called directly without the scheduler.
        """
        try:
            # Delete all existing pools to start fresh
            all_pools = TimePool.query.all()
            pool_count = len(all_pools)
            for pool in all_pools:
                db.session.delete(pool)
            db.session.commit()
            self.logger.info(f"Deleted {pool_count} existing time pools")
            
            # Find date range based on actual events (limited to max_days_ahead)
            earliest_event = db.session.query(Event.start_time).order_by(Event.start_time.asc()).first()
            latest_event = db.session.query(Event.start_time).order_by(Event.start_time.desc()).first()
            
            if not earliest_event or not latest_event:
                self.logger.info(f"No events found - creating pools for next {max_days_ahead} days")
                start_date = datetime.now().date()
                end_date = start_date + timedelta(days=max_days_ahead)
            else:
                # Include actual event dates but limit future generation
                start_date = min(earliest_event[0].date(), datetime.now().date())
                max_future_date = datetime.now().date() + timedelta(days=max_days_ahead)
                end_date = min(latest_event[0].date(), max_future_date)
            
            self.logger.info(f"Regenerating time pools from {start_date} to {end_date}")
            
            pools_created = 0
            pools_updated = 0
            
            # Process each day in the range
            current_date = start_date
            while current_date <= end_date:
                day_pools_created, day_pools_updated = self._generate_pools_for_date(
                    current_date, 6, 23, 30
                )
                pools_created += day_pools_created
                pools_updated += day_pools_updated
                current_date += timedelta(days=1)
            
            db.session.commit()
            self.logger.info(f"Full regeneration complete: {pools_created} pools created, {pools_updated} updated")
            
            # Regenerate task assignments after pool regeneration
            self._regenerate_task_assignments(context="full_regeneration")
            
            return pools_created, pools_updated
            
        except Exception as e:
            self.logger.error(f"Error during full regeneration: {e}")
            db.session.rollback()
            raise
    
    def update_time_pools_for_range(self, start_date: date, end_date: date) -> Tuple[int, int]:
        """
        Update time pools for a specific date range.
        More efficient than full regeneration for smaller ranges.
        """
        try:
            self.logger.info(f"Updating time pools from {start_date} to {end_date}")
            
            # Delete existing pools for this date range
            existing_pools = TimePool.query.filter(
                TimePool.pool_date >= start_date,
                TimePool.pool_date <= end_date
            ).all()
            
            pool_count = len(existing_pools)
            for pool in existing_pools:
                db.session.delete(pool)
            
            self.logger.info(f"Deleted {pool_count} existing pools in date range")
            
            pools_created = 0
            pools_updated = 0
            
            # Process each day in the range
            current_date = start_date
            while current_date <= end_date:
                day_pools_created, day_pools_updated = self._generate_pools_for_date(
                    current_date, 6, 23, 30
                )
                pools_created += day_pools_created
                pools_updated += day_pools_updated
                current_date += timedelta(days=1)
            
            db.session.commit()
            self.logger.info(f"Range update complete: {pools_created} pools created, {pools_updated} updated")
            
            # Regenerate task assignments after range update
            self._regenerate_task_assignments(context="range_update")
            
            return pools_created, pools_updated
            
        except Exception as e:
            self.logger.error(f"Error updating pools for range: {e}")
            db.session.rollback()
            raise
    
    def _regenerate_task_assignments(self, context: str = "scheduled"):
        """
        Regenerate task assignments after time pool changes.
        Uses the existing bulk assignment system to reassign all tasks.
        """
        try:
            assignment_service = get_assignment_service()
            
            result = assignment_service.bulk_assign_tasks_to_pools(
                clear_existing=True,
                max_days_ahead=7,
                assigned_by=f'auto_{context}'
            )
            
            if result['success']:
                self.logger.info(f"Task assignment regeneration ({context}): {result['message']}")
                return result
            else:
                self.logger.error(f"Task assignment regeneration failed ({context}): {result['message']}")
                return result
                
        except Exception as e:
            self.logger.error(f"Error regenerating task assignments ({context}): {e}")
            return {
                'success': False,
                'message': f"Assignment regeneration failed: {str(e)}",
                'assignments_made': [],
                'tasks_processed': 0,
                'pools_used': 0,
                'unassigned_tasks': []
            }
    
    def get_status(self):
        """Get time pool service status"""
        try:
            today = datetime.now().date()
            total_pools = TimePool.query.count()
            future_pools = TimePool.query.filter(TimePool.pool_date >= today).count()
            available_pools = TimePool.query.filter(
                and_(TimePool.pool_date >= today, TimePool.available_minutes > 0)
            ).count()
            
            return {
                'total_time_pools': total_pools,
                'future_pools': future_pools,
                'available_pools': available_pools,
                'service_healthy': total_pools > 0
            }
        except Exception as e:
            self.logger.error(f"Error getting time pool status: {e}")
            return {
                'total_time_pools': 0,
                'future_pools': 0,
                'available_pools': 0,
                'service_healthy': False,
                'error': str(e)
            }