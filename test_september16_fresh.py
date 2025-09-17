#!/usr/bin/env python3
"""
Force regenerate September 16th time pools
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

from app import create_app
from models import db, Event, TimePool
from background_service import background_service
from datetime import date

def test_september16_fresh():
    app = create_app()
    
    with app.app_context():
        background_service.init_app(app)
        
        print("=== Force Regenerating September 16th Time Pools ===\n")
        
        target_date = date(2025, 9, 16)
        
        # Delete existing pools for this date
        existing_pools = TimePool.query.filter(TimePool.pool_date == target_date).all()
        print(f"Deleting {len(existing_pools)} existing pools for {target_date}")
        for pool in existing_pools:
            db.session.delete(pool)
        db.session.commit()
        
        # Force regenerate for this specific date
        print(f"Regenerating pools for {target_date}...")
        pools_created, pools_updated = background_service._generate_pools_for_date(target_date, 6, 23, 30)
        
        print(f"Pools created: {pools_created}, updated: {pools_updated}")
        
        # Check results
        pools = TimePool.query.filter(TimePool.pool_date == target_date).order_by(TimePool.start_time).all()
        
        print(f"\nTime Pools for {target_date}:")
        if pools:
            for i, pool in enumerate(pools, 1):
                work_type = "Work" if pool.is_work_time else "Personal"
                context = ', '.join(pool.get_context_tags_list())
                print(f"  Pool {i}: {pool.start_time.strftime('%H:%M')} - {pool.end_time.strftime('%H:%M')}")
                print(f"    Duration: {pool.total_minutes} minutes ({pool.total_minutes/60:.1f} hours)")
                print(f"    Type: {work_type}")
                print(f"    Context: {context}")
                print()
        else:
            print("  No time pools found")

if __name__ == "__main__":
    test_september16_fresh()