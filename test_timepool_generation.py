#!/usr/bin/env python3
"""
Test script for time pool generation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

from app import create_app
from models import db, Event, TimePool
from background_service import background_service

def test_time_pool_generation():
    app = create_app()
    
    with app.app_context():
        # Initialize background service
        background_service.init_app(app)
        
        print("=== TaskMaster Time Pool Generation Test ===\n")
        
        # Check existing events
        events = Event.query.all()
        print(f"Events in database: {len(events)}")
        
        for i, event in enumerate(events[:5]):
            print(f"  {i+1}. {event.title}")
            print(f"     {event.start_time} to {event.end_time}")
            print(f"     Blocking: {event.is_blocking}")
        
        if len(events) > 5:
            print(f"     ... and {len(events) - 5} more")
        
        print("\n" + "="*50)
        print("Generating time pools...")
        
        # Clean existing pools first
        existing_pools = TimePool.query.all()
        print(f"Removing {len(existing_pools)} existing time pools...")
        for pool in existing_pools:
            db.session.delete(pool)
        db.session.commit()
        
        # Generate new pools
        background_service._generate_time_pools()
        
        # Check results
        pools = TimePool.query.order_by(TimePool.start_time).all()
        print(f"\nTime pools created: {len(pools)}")
        
        if pools:
            print("\nFirst 10 time pools:")
            for i, pool in enumerate(pools[:10]):
                tags = pool.get_context_tags_list()
                work_type = "Work" if pool.is_work_time else "Personal"
                print(f"  {i+1}. {pool.pool_date} {pool.start_time.strftime('%H:%M')} - {pool.end_time.strftime('%H:%M')}")
                print(f"     Duration: {pool.total_minutes} minutes ({work_type})")
                print(f"     Context: {', '.join(tags)}")
        
        # Summary by date
        print("\n" + "="*50)
        print("Summary by date:")
        
        from collections import defaultdict
        pools_by_date = defaultdict(list)
        for pool in pools:
            pools_by_date[pool.pool_date].append(pool)
        
        for date, date_pools in sorted(pools_by_date.items()):
            total_minutes = sum(p.total_minutes for p in date_pools)
            work_minutes = sum(p.total_minutes for p in date_pools if p.is_work_time)
            personal_minutes = total_minutes - work_minutes
            
            print(f"  {date}: {len(date_pools)} pools, {total_minutes} total minutes")
            print(f"    Work: {work_minutes}min, Personal: {personal_minutes}min")
        
        print("\n" + "="*50)
        print("Test completed successfully!")

if __name__ == "__main__":
    test_time_pool_generation()