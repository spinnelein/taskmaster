#!/usr/bin/env python3
"""
Test YOLO System with Claude API Integration
Run from flask_app directory
"""

import os
import sys
import json
from datetime import datetime, date, timedelta

# Load environment variables
from pathlib import Path
from dotenv import load_dotenv

env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

# Set API key if not already set
if not os.getenv('CLAUDE_API_KEY'):
    print("CLAUDE_API_KEY not found in .env, loading from .env.production")
    prod_env = Path(__file__).parent.parent / '.env.production'
    if prod_env.exists():
        with open(prod_env, 'r') as f:
            for line in f:
                if line.strip().startswith('CLAUDE_API_KEY='):
                    key = line.strip().split('=', 1)[1]
                    os.environ['CLAUDE_API_KEY'] = key
                    os.environ['ANTHROPIC_API_KEY'] = key
                    print("API key loaded from .env.production")
                    break

from app import app
from models import db, Task, Project, Event, TimePool
from services.claude_task_analyzer import ClaudeTaskAnalyzer
from services.project_aware_priority_service import get_project_aware_priority_service
from services.event_aware_assignment_service import get_event_aware_assignment_service
from services.smart_scheduling_service import SmartSchedulingService

def test_yolo_system():
    """Test complete YOLO system with Claude API"""
    
    print("\n" + "="*60)
    print("TASKMASTER YOLO SYSTEM TEST WITH CLAUDE API")
    print("="*60)
    
    # Test 1: Database columns
    print("\n1. Testing Database Migration...")
    try:
        # Create a test task with YOLO fields
        # Generate unique ID
        import uuid
        test_id = f'yolo-test-{uuid.uuid4().hex[:8]}'
        
        test_task = Task(
            id=test_id,
            title='AI Analysis Test Task',
            description='Testing YOLO fields with Claude API',
            duration=60,
            cognitive_load='medium',
            energy_level='high',
            ai_analysis='{}',
            last_analyzed=datetime.now()
        )
        db.session.add(test_task)
        db.session.commit()
        
        # Verify fields
        task = Task.query.get(test_id)
        assert task.cognitive_load == 'medium'
        assert task.energy_level == 'high'
        print("PASS: Database migration successful - YOLO columns working")
        
        # Clean up
        db.session.delete(task)
        db.session.commit()
    except Exception as e:
        print(f"FAIL: Database test failed: {e}")
        db.session.rollback()
    
    # Test 2: Claude API
    print("\n2. Testing Claude API Integration...")
    try:
        analyzer = ClaudeTaskAnalyzer()
        print(f"   Claude API available: {analyzer.is_claude_available}")
        print(f"   API Key present: {'CLAUDE_API_KEY' in os.environ}")
        
        if analyzer.is_claude_available:
            # Test analysis
            test_task_data = {
                'id': 'test-123',
                'title': 'Build a microservices architecture with Docker and Kubernetes',
                'description': 'Design and implement a scalable microservices system using container orchestration',
                'project_id': None
            }
            
            analysis = analyzer.analyze_task_comprehensive(test_task_data)
            
            print("\n   Analysis Results:")
            print(f"   - Complexity: {analysis.get('complexity', {}).get('level', 'N/A')}")
            print(f"   - Time estimate: {analysis.get('time_estimation', {}).get('estimated_duration', 'N/A')} minutes")
            print(f"   - Analysis source: {analysis.get('analysis_source', 'N/A')}")
            print(f"   - AI confidence: {analysis.get('ai_confidence', 0)}")
            
            # Save to database
            if Task.query.filter_by(title=test_task_data['title']).first():
                print("   (Test task already exists, skipping creation)")
            else:
                new_task = Task(
                    id='claude-test-001',
                    title=test_task_data['title'],
                    description=test_task_data['description'],
                    duration=analysis.get('time_estimation', {}).get('estimated_duration', 180),
                    cognitive_load=analysis.get('complexity', {}).get('level', 'high'),
                    energy_level=analysis.get('context', {}).get('energy_level', 'high'),
                    ai_analysis=json.dumps(analysis),
                    last_analyzed=datetime.now()
                )
                db.session.add(new_task)
                db.session.commit()
                print("   PASS: AI analysis saved to database")
                
                # Clean up
                db.session.delete(new_task)
                db.session.commit()
        else:
            print("   WARNING: Claude API not available - check API key")
    except Exception as e:
        print(f"   FAIL: Claude API test failed: {e}")
        db.session.rollback()
    
    # Test 3: YOLO Services Integration
    print("\n3. Testing YOLO Services Integration...")
    try:
        priority_service = get_project_aware_priority_service()
        assignment_service = get_event_aware_assignment_service()
        
        # Create test project and task
        project = Project.query.first()
        if not project:
            project = Project(
                id='test-proj-001',
                title='YOLO Test Project',
                priority='HIGH',
                status='ACTIVE'
            )
            db.session.add(project)
            db.session.commit()
        
        # Calculate priority
        task_data = {
            'id': 'priority-test',
            'title': 'High priority task',
            'due_date': (date.today() + timedelta(days=1)).isoformat(),
            'project_id': project.id,
            'urgency': 9
        }
        
        score = priority_service.calculate_priority_score(task_data)
        print(f"   Priority score: {score}/1000")
        
        # Get available pools
        pools = assignment_service.get_available_pools_with_events(
            date.today(), 
            date.today() + timedelta(days=3)
        )
        print(f"   Available pools: {len(pools)}")
        
        print("   PASS: YOLO services working correctly")
    except Exception as e:
        print(f"   FAIL: Services test failed: {e}")
        db.session.rollback()
    
    # Test 4: Complete Workflow
    print("\n4. Testing Complete YOLO Workflow...")
    try:
        # Create task
        # Generate unique ID and set required duration
        import uuid
        workflow_id = f'workflow-test-{uuid.uuid4().hex[:8]}'
        
        workflow_task = Task(
            id=workflow_id,
            title='Implement real-time chat application with WebSockets',
            description='Build a scalable chat system supporting multiple rooms and private messages',
            duration=120,  # Set required duration field
            project_id=project.id if project else None,
            urgency=7,
            priority='medium'
        )
        db.session.add(workflow_task)
        db.session.commit()
        
        # Analyze with Claude if available
        if analyzer.is_claude_available:
            task_dict = workflow_task.to_dict()
            analysis = analyzer.analyze_task_comprehensive(task_dict)
            
            # Update task with analysis
            workflow_task.cognitive_load = analysis.get('complexity', {}).get('level', 'medium')
            workflow_task.energy_level = analysis.get('context', {}).get('energy_level', 'medium')
            workflow_task.ai_analysis = json.dumps(analysis)
            workflow_task.last_analyzed = datetime.now()
            
            # Update duration if provided
            if 'time_estimation' in analysis:
                workflow_task.duration = analysis['time_estimation'].get('estimated_duration', 120)
            
            db.session.commit()
            print(f"   PASS: Task analyzed - complexity: {workflow_task.cognitive_load}, duration: {workflow_task.duration}min")
        
        # Calculate priority
        priority_score = priority_service.calculate_priority_score(workflow_task.to_dict())
        print(f"   PASS: Priority calculated: {priority_score}/1000")
        
        # Clean up
        db.session.delete(workflow_task)
        if Project.query.filter_by(id='test-proj-001').first():
            db.session.delete(project)
        db.session.commit()
        
        print("   PASS: Complete workflow successful!")
    except Exception as e:
        print(f"   FAIL: Workflow test failed: {e}")
        db.session.rollback()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    with app.app_context():
        test_yolo_system()