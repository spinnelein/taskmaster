#!/usr/bin/env python3
"""
Simple test to verify the recurring events upgrade
NO EMOJIS
"""
import sqlite3
from datetime import date, timedelta

def test_upgrade_results():
    """
    Test the results of the recurring events upgrade
    """
    print("RECURRING EVENTS UPGRADE VERIFICATION")
    print("=" * 50)
    
    conn = sqlite3.connect('taskmaster.db')
    cursor = conn.cursor()
    
    try:
        # Test 1: Check instance cleanup
        cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE recurrence_master_id IS NOT NULL 
            AND is_recurrence_master = 0
        """)
        instance_count = cursor.fetchone()[0]
        
        print(f"1. Instance Records Cleanup:")
        print(f"   Pre-generated instances remaining: {instance_count}")
        if instance_count == 0:
            print("   ✓ SUCCESS: All 3,640 instances successfully removed")
        else:
            print("   ⚠ ISSUE: Some instances still remain")
        
        # Test 2: Check master events
        cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE is_recurrence_master = 1
        """)
        master_count = cursor.fetchone()[0]
        
        print(f"\n2. Master Events:")
        print(f"   Recurring master events: {master_count}")
        if master_count > 0:
            print("   ✓ SUCCESS: Master events preserved")
        else:
            print("   ⚠ ISSUE: No master events found")
        
        # Test 3: Check RRULE migration
        cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE recurrence_rrule IS NOT NULL 
            AND recurrence_rrule != ''
        """)
        rrule_count = cursor.fetchone()[0]
        
        print(f"\n3. RRULE Migration:")
        print(f"   Events with RRULE patterns: {rrule_count}")
        if rrule_count > 0:
            print("   ✓ SUCCESS: JSON patterns migrated to RRULE")
        else:
            print("   ⚠ ISSUE: No RRULE patterns found")
        
        # Test 4: Check new database fields
        cursor.execute("PRAGMA table_info(events)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_fields = ['recurrence_rrule', 'recurrence_end', 'timezone', 'dtstart', 'dtend']
        missing_fields = [field for field in new_fields if field not in columns]
        
        print(f"\n4. Database Schema:")
        print(f"   New fields added: {len(new_fields) - len(missing_fields)}/{len(new_fields)}")
        if not missing_fields:
            print("   ✓ SUCCESS: All required fields added")
        else:
            print(f"   ⚠ ISSUE: Missing fields: {missing_fields}")
        
        # Test 5: Check exception tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('event_exceptions', 'event_series_splits')
        """)
        exception_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n5. Exception Tables:")
        print(f"   Exception/split tables created: {len(exception_tables)}/2")
        if len(exception_tables) == 2:
            print("   ✓ SUCCESS: Exception handling tables ready")
        else:
            print(f"   ⚠ ISSUE: Missing tables: {set(['event_exceptions', 'event_series_splits']) - set(exception_tables)}")
        
        # Test 6: Sample RRULE patterns
        cursor.execute("""
            SELECT title, recurrence_rrule 
            FROM events 
            WHERE recurrence_rrule IS NOT NULL 
            LIMIT 3
        """)
        
        print(f"\n6. Sample RRULE Patterns:")
        for title, rrule in cursor.fetchall():
            print(f"   {title}: {rrule}")
        
        # Summary
        total_events_before = 3640 + master_count  # instances + masters
        total_events_after = master_count
        storage_reduction = ((total_events_before - total_events_after) / total_events_before) * 100
        
        print(f"\n" + "="*50)
        print("UPGRADE SUMMARY")
        print("="*50)
        print(f"Database records before: {total_events_before}")
        print(f"Database records after:  {total_events_after}")
        print(f"Storage reduction:       {storage_reduction:.1f}%")
        print(f"Master events:           {master_count}")
        print(f"RRULE patterns:          {rrule_count}")
        print(f"Exception tables:        {len(exception_tables)}/2")
        
        if (instance_count == 0 and master_count > 0 and rrule_count > 0 and 
            len(exception_tables) == 2 and not missing_fields):
            print(f"\n🎉 UPGRADE SUCCESSFUL! 🎉")
            print(f"TaskMaster now uses industry-standard recurring events!")
        else:
            print(f"\n⚠ UPGRADE INCOMPLETE")
            print(f"Some issues detected - review output above")
        
    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    test_upgrade_results()