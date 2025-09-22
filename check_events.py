import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('taskmaster.db')
cursor = conn.cursor()

# Get current time info
now = datetime.now()
print(f'Current time: {now}')
print(f'Current time ISO: {now.isoformat()}')
print(f'Current time str: {str(now)}')

# Check for events in next hour
next_hour = now + timedelta(hours=1)
cursor.execute("""
    SELECT id, title, start_time, notifications_enabled 
    FROM events 
    WHERE start_time >= ? AND start_time < ?
    ORDER BY start_time
""", (str(now), str(next_hour)))

print('\nEvents in next hour:')
for event in cursor.fetchall():
    print(f'  {event[1]}: {event[2]} (notifications: {event[3]})')

# Check what format the dates are stored in
cursor.execute("SELECT start_time FROM events LIMIT 1")
sample_time = cursor.fetchone()[0]
print(f'\nSample stored time format: {sample_time}')
print(f'Type: {type(sample_time)}')

# Test the query with different formats
start_time = now.replace(second=0, microsecond=0)
end_time = start_time + timedelta(minutes=1)

print(f'\nTesting query with ISO format:')
print(f'  Start: {start_time.isoformat()}')
print(f'  End: {end_time.isoformat()}')

cursor.execute("""
    SELECT COUNT(*) FROM events 
    WHERE start_time >= ? 
    AND start_time < ?
""", (start_time.isoformat(), end_time.isoformat()))
count_iso = cursor.fetchone()[0]
print(f'  Results: {count_iso}')

print(f'\nTesting query with string format:')
print(f'  Start: {str(start_time)}')
print(f'  End: {str(end_time)}')

cursor.execute("""
    SELECT COUNT(*) FROM events 
    WHERE start_time >= ? 
    AND start_time < ?
""", (str(start_time), str(end_time)))
count_str = cursor.fetchone()[0]
print(f'  Results: {count_str}')

conn.close()