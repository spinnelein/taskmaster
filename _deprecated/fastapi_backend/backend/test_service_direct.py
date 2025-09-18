#!/usr/bin/env python3
"""
Direct test of the recurring events service
"""
import sys
import os
from datetime import date, timedelta
import sqlite3

def test_direct_service():
    print("Direct Service Test")
    print("=" * 30)
    
    # Get event data directly from database
    conn = sqlite3.connect('taskmaster.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, start_time, end_time, recurrence_rrule, is_recurrence_master
        FROM events 
        WHERE is_recurrence_master = 1 
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if not row:
        print("No master events found!")
        return False
    
    event_id, title, start_time, end_time, rrule, is_master = row
    print(f"Testing event: {title}")
    print(f"RRULE: {rrule}")
    print(f"Start time: {start_time}")
    print(f"Is master: {is_master}")
    
    conn.close()
    
    # Test the RRULE parsing directly
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from utils.recurrence import generate_occurrences_from_rrule
        from datetime import datetime
        
        # Convert strings to datetime objects
        dtstart = datetime.fromisoformat(start_time.replace('Z', '+00:00')) if 'Z' in start_time else datetime.fromisoformat(start_time)
        dtend = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if 'Z' in end_time else datetime.fromisoformat(end_time)
        
        start_range = date.today()
        end_range = start_range + timedelta(days=7)
        
        print(f"\nGenerating occurrences from {start_range} to {end_range}")
        
        # Test direct RRULE expansion
        occurrences = generate_occurrences_from_rrule(
            dtstart=dtstart,
            dtend=dtend,
            rrule_string=rrule,
            start_range=start_range,
            end_range=end_range,
            max_occurrences=10
        )
        
        print(f"Generated {len(occurrences)} occurrences:")
        for i, occ in enumerate(occurrences[:5]):
            print(f"  {i+1}. {occ['occurrence_date']} - {occ['start'].strftime('%H:%M')}")
        
        if len(occurrences) > 0:
            print("SUCCESS: RRULE expansion working!")
            return True
        else:
            print("ISSUE: No occurrences generated")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_service()
    if success:
        print("\nDirect service test PASSED")
    else:
        print("\nDirect service test FAILED")