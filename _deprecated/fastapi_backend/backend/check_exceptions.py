import sqlite3

conn = sqlite3.connect('taskmaster.db')
cursor = conn.cursor()

# Check exceptions
cursor.execute('SELECT * FROM event_exceptions')
rows = cursor.fetchall()
print(f'Found {len(rows)} exceptions:')
for row in rows:
    print(row)

conn.close()