#!/usr/bin/env python3
"""Debug script to check task queue service"""

import sys
import os

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

from flask import Flask
from models import db
from task_queue_service import get_task_queue_service

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_app/taskmaster.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    queue_service = get_task_queue_service()
    
    print("=== ALL TASKS QUEUE ===")
    all_tasks = queue_service.get_all_tasks_queue(limit=10)
    print(f"Found {len(all_tasks)} tasks in all_tasks_queue")
    
    for i, task_item in enumerate(all_tasks):
        print(f"\nTask {i+1}: {task_item.get('title', 'Unknown')}")
        print(f"  Status: {task_item.get('status')}")
        print(f"  Can be scheduled: {task_item.get('can_be_scheduled')}")
        print(f"  Blocking reasons: {task_item.get('blocking_reasons')}")
        print(f"  Is assigned: {task_item.get('is_assigned')}")
        print(f"  Is fully assigned: {task_item.get('is_fully_assigned')}")
        print(f"  Remaining minutes: {task_item.get('remaining_minutes')}")
        print(f"  Priority score: {task_item.get('priority_score')}")
    
    print("\n=== AVAILABLE TASKS QUEUE ===")
    available_tasks = queue_service.get_available_tasks_queue(limit=10)
    print(f"Found {len(available_tasks)} tasks in available_tasks_queue")
    
    for i, task_item in enumerate(available_tasks):
        print(f"\nAvailable Task {i+1}: {task_item.get('title', 'Unknown')}")
        print(f"  Can be scheduled: {task_item.get('can_be_scheduled')}")
        print(f"  Is fully assigned: {task_item.get('is_fully_assigned')}")
        print(f"  Priority score: {task_item.get('priority_score')}")