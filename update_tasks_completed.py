#!/usr/bin/env python3
"""
Script to update all tasks to set is_completed = 0
"""

import sys
import os

# Add the research directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'research'))

from app import app
from models import db, Task
from sqlalchemy import text

def update_tasks():
    with app.app_context():
        try:
            # Update all tasks to set is_completed = 0
            result = db.session.execute(text('UPDATE tasks SET is_completed = 0'))
            db.session.commit()
            
            # Get count of updated rows
            count = result.rowcount
            print(f'Successfully updated {count} tasks to set is_completed = 0')
            
            # Verify by counting completed tasks
            completed_count = Task.query.filter(Task.is_completed == True).count()
            total_count = Task.query.count()
            print(f'Verification: {completed_count} completed tasks out of {total_count} total tasks')
            
            return True
            
        except Exception as e:
            print(f'Error updating tasks: {e}')
            db.session.rollback()
            return False

if __name__ == '__main__':
    print('Updating all tasks to set is_completed = 0...')
    success = update_tasks()
    if success:
        print('Update completed successfully!')
    else:
        print('Update failed!')
        sys.exit(1)