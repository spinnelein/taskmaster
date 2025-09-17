#!/usr/bin/env python3
"""
Test bulk time pool regeneration with fixed method
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

from app import create_app
from models import db, Event, TimePool
from background_service import background_service
from datetime import date, timedelta

def test_bulk_regeneration():
    app = create_app()
    
    with app.app_context():
        background_service.init_app(app)
        
        print("=== Time Pool Bulk Regeneration Test ===\n")
        
        # Check current state
        current_pools = TimePool.query.count()
        print(f"Current time pools in database: {current_pools}")
        
        # Show a few examples of current pools
        sample_pools = TimePool.query.order_by(TimePool.pool_date, TimePool.start_time).limit(5).all()
        if sample_pools:
            print("\nSample of current pools:")
            for pool in sample_pools:
                context = ', '.join(pool.get_context_tags_list())
                work_type = "Work" if pool.is_work_time else "Personal"
                print(f"  {pool.pool_date}: {pool.start_time.strftime('%H:%M')}-{pool.end_time.strftime('%H:%M')} "
                      f"({pool.total_minutes}min, {work_type}) [{context}]")
        
        # Test regeneration for limited range (next 7 days)
        print(f"\n=== Testing Range Update (7 days from today) ===")
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        pools_created, pools_updated = background_service.update_time_pools_for_range(start_date, end_date)
        print(f"Range update result: {pools_created} created, {pools_updated} updated")
        
        # Check results for the range
        range_pools = TimePool.query.filter(
            TimePool.pool_date >= start_date,
            TimePool.pool_date <= end_date
        ).order_by(TimePool.pool_date, TimePool.start_time).all()
        
        print(f"\nNew pools created in range ({len(range_pools)} total):")
        for pool in range_pools:
            context = ', '.join(pool.get_context_tags_list())
            work_type = "Work" if pool.is_work_time else "Personal"
            weather_info = ""
            if pool.weather_forecast_id:
                weather_info = " [Weather linked]"
            print(f"  {pool.pool_date}: {pool.start_time.strftime('%H:%M')}-{pool.end_time.strftime('%H:%M')} "
                  f"({pool.total_minutes}min, {work_type}){weather_info}")
            print(f"    Context: {context}")
        
        # Final count
        final_pools = TimePool.query.count()
        print(f"\nFinal time pools in database: {final_pools}")
        print(f"Net change: {final_pools - current_pools:+d} pools")

if __name__ == "__main__":
    test_bulk_regeneration()