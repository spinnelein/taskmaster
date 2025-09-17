#!/usr/bin/env python3
"""
Focused test for September 12th time pools
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

from app import create_app
from models import db, Event, TimePool
from background_service import background_service

def test_september12_pools():
    app = create_app()
    
    with app.app_context():
        background_service.init_app(app)
        
        print("=== September 12th Time Pool Analysis ===\n")
        
        # Get September 12th events
        from datetime import datetime, date
        target_date = date(2025, 9, 12)
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date, datetime.max.time())
        
        events = Event.query.filter(
            Event.start_time >= day_start,
            Event.start_time <= day_end
        ).order_by(Event.start_time).all()
        
        print(f"Events on {target_date}:")
        for event in events:
            blocking = "BLOCKING" if event.is_blocking else "non-blocking"
            print(f"  {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M') if event.end_time else 'Unknown'}: {event.title} ({blocking})")
        
        # Get time pools for September 12th
        pools = TimePool.query.filter(TimePool.pool_date == target_date).order_by(TimePool.start_time).all()
        
        print(f"\nTime Pools created for {target_date}:")
        if pools:
            for i, pool in enumerate(pools, 1):
                work_type = "Work" if pool.is_work_time else "Personal"
                context = ', '.join(pool.get_context_tags_list())
                print(f"  Pool {i}: {pool.start_time.strftime('%H:%M')} - {pool.end_time.strftime('%H:%M')}")
                print(f"    Duration: {pool.total_minutes} minutes ({pool.total_minutes/60:.1f} hours)")
                print(f"    Type: {work_type}")
                print(f"    Context: {context}")
                print(f"    Available: {pool.available_minutes} minutes")
                print()
        else:
            print("  No time pools found")
        
        # Show gaps analysis
        print("Gap Analysis:")
        print("=============")
        
        # Manual gap calculation for verification
        blocking_events = [e for e in events if e.is_blocking]
        blocking_events.sort(key=lambda x: x.start_time)
        
        work_start = datetime.combine(target_date, datetime.min.time().replace(hour=6))
        work_end = datetime.combine(target_date, datetime.min.time().replace(hour=23))
        
        print(f"Work day: {work_start.strftime('%H:%M')} - {work_end.strftime('%H:%M')}")
        print(f"Blocking events:")
        
        current_time = work_start
        for event in blocking_events:
            if event.start_time > current_time:
                gap_minutes = (event.start_time - current_time).total_seconds() / 60
                print(f"  GAP: {current_time.strftime('%H:%M')} - {event.start_time.strftime('%H:%M')} ({gap_minutes:.0f} minutes)")
            
            print(f"  EVENT: {event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M') if event.end_time else 'Unknown'}: {event.title}")
            current_time = max(current_time, event.end_time if event.end_time else event.start_time)
        
        # Final gap
        if current_time < work_end:
            gap_minutes = (work_end - current_time).total_seconds() / 60
            print(f"  GAP: {current_time.strftime('%H:%M')} - {work_end.strftime('%H:%M')} ({gap_minutes:.0f} minutes)")

if __name__ == "__main__":
    test_september12_pools()