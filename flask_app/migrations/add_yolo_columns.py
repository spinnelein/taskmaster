#!/usr/bin/env python3
"""
Database migration to add YOLO AI analysis columns
As specified in yolo.md Phase 3
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add YOLO columns to tasks and time_pools tables"""
    
    with app.app_context():
        try:
            # Get database connection
            conn = db.session.connection()
            
            # Check if columns already exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_task_columns = [col['name'] for col in inspector.get_columns('tasks')]
            existing_pool_columns = [col['name'] for col in inspector.get_columns('time_pools_flask')]
            
            logger.info(f"Existing task columns: {existing_task_columns}")
            logger.info(f"Existing pool columns: {existing_pool_columns}")
            
            # Add columns to tasks table if they don't exist
            columns_to_add = [
                ('cognitive_load', 'VARCHAR(20)'),
                ('ai_analysis', 'TEXT'),
                ('last_analyzed', 'TIMESTAMP'),
                ('energy_level', 'VARCHAR(20)')
            ]
            
            for column_name, column_type in columns_to_add:
                if column_name not in existing_task_columns:
                    logger.info(f"Adding column {column_name} to tasks table...")
                    query = text(f'ALTER TABLE tasks ADD COLUMN {column_name} {column_type}')
                    conn.execute(query)
                    logger.info(f"Successfully added {column_name}")
                else:
                    logger.info(f"Column {column_name} already exists in tasks table")
            
            # Add context_tags to time_pools_flask if it doesn't exist
            if 'context_tags' not in existing_pool_columns:
                logger.info("Adding context_tags column to time_pools_flask table...")
                query = text('ALTER TABLE time_pools_flask ADD COLUMN context_tags TEXT')
                conn.execute(query)
                logger.info("Successfully added context_tags to time_pools_flask")
            else:
                logger.info("Column context_tags already exists in time_pools_flask table")
            
            # Commit changes
            db.session.commit()
            logger.info("Migration completed successfully!")
            
            # Verify columns were added
            new_task_columns = [col['name'] for col in inspector.get_columns('tasks')]
            new_pool_columns = [col['name'] for col in inspector.get_columns('time_pools_flask')]
            
            logger.info(f"Task columns after migration: {new_task_columns}")
            logger.info(f"Pool columns after migration: {new_pool_columns}")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    logger.info("Starting YOLO database migration...")
    success = run_migration()
    if success:
        logger.info("Migration completed successfully!")
    else:
        logger.error("Migration failed!")
        sys.exit(1)