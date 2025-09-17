# Test Performance with Larger Date Ranges
# NO EMOJIS

import requests
import time
from datetime import date, timedelta
import statistics

BASE_URL = "http://localhost:8000"

def test_performance():
    """Test expansion performance with various date ranges"""
    
    print("=== Testing Expansion Performance ===\n")
    
    # Get a recurring event
    response = requests.get(f"{BASE_URL}/api/events")
    events = response.json()["events"]
    recurring_events = [e for e in events if e["is_recurring"]]
    
    if not recurring_events:
        print("ERROR: No recurring events found!")
        return
    
    # Use the first recurring event
    event = recurring_events[0]
    event_id = event["id"]
    print(f"Testing with event: {event['title']} (ID: {event_id})")
    print(f"Recurrence pattern: {event['recurrence_pattern']['pattern']}")
    print()
    
    # Test different date ranges
    test_ranges = [
        ("1 week", 7),
        ("1 month", 30),
        ("3 months", 90),
        ("6 months", 180),
        ("1 year", 365),
        ("2 years", 730)
    ]
    
    results = []
    
    for range_name, days in test_ranges:
        print(f"Testing {range_name} range ({days} days)...")
        
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        
        # Run multiple times for average
        times = []
        occurrence_counts = []
        
        for i in range(5):
            start_time = time.time()
            
            response = requests.get(
                f"{BASE_URL}/api/events/expand/{event_id}",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "max_occurrences": 1000
                }
            )
            
            end_time = time.time()
            elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                data = response.json()
                times.append(elapsed)
                occurrence_counts.append(data["total_occurrences"])
            else:
                print(f"  ERROR: {response.status_code}")
                break
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            occurrences = occurrence_counts[0]  # Should be the same for all
            
            results.append({
                "range": range_name,
                "days": days,
                "occurrences": occurrences,
                "avg_time": avg_time,
                "min_time": min_time,
                "max_time": max_time
            })
            
            print(f"  Occurrences: {occurrences}")
            print(f"  Average time: {avg_time:.2f}ms")
            print(f"  Min/Max: {min_time:.2f}ms / {max_time:.2f}ms")
            print()
    
    # Summary
    print("\n=== Performance Summary ===")
    print(f"{'Range':<12} {'Days':<6} {'Occurrences':<12} {'Avg Time':<12} {'Min Time':<12} {'Max Time':<12}")
    print("-" * 78)
    
    for r in results:
        print(f"{r['range']:<12} {r['days']:<6} {r['occurrences']:<12} "
              f"{r['avg_time']:<12.2f} {r['min_time']:<12.2f} {r['max_time']:<12.2f}")
    
    # Performance analysis
    print("\n=== Performance Analysis ===")
    if len(results) >= 2:
        # Calculate time per occurrence
        for r in results:
            if r['occurrences'] > 0:
                time_per_occ = r['avg_time'] / r['occurrences']
                print(f"{r['range']}: {time_per_occ:.3f}ms per occurrence")
        
        # Check scalability
        if results[-1]['occurrences'] > 0 and results[0]['occurrences'] > 0:
            scale_factor = results[-1]['occurrences'] / results[0]['occurrences']
            time_factor = results[-1]['avg_time'] / results[0]['avg_time']
            
            print(f"\nScaling: {scale_factor:.1f}x more occurrences = {time_factor:.1f}x more time")
            
            if time_factor < scale_factor:
                print("GOOD: Performance scales better than linearly!")
            elif time_factor > scale_factor * 1.5:
                print("WARNING: Performance degrades worse than linearly")
            else:
                print("OK: Performance scales approximately linearly")
    
    # Test with exceptions
    print("\n=== Testing with Exceptions ===")
    
    # We know we have exceptions for event d77aaa83-2dcf-4097-a6d3-d04f2571d54e
    if event_id == "d77aaa83-2dcf-4097-a6d3-d04f2571d54e":
        print("Testing expansion with known exceptions...")
        
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/api/events/expand/{event_id}",
            params={
                "start_date": "2025-09-15",
                "end_date": "2025-09-22",
                "max_occurrences": 10
            }
        )
        elapsed = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Occurrences: {data['total_occurrences']} (with exceptions applied)")
            print(f"  Time: {elapsed:.2f}ms")
            
            # Count exceptions
            exception_count = sum(1 for occ in data["occurrences"] if occ["is_exception"])
            print(f"  Modified occurrences: {exception_count}")


if __name__ == "__main__":
    test_performance()