"""
Smart Scheduling API Routes - YOLO.md Phase 2 Implementation

Handles intelligent scheduling endpoints including daily routines,
project-aware task assignment, and weekly optimization.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
from models import db, Task, Project, ProjectPhase, TimePool
from services.smart_scheduling_service import SmartSchedulingService
from services.claude_task_analyzer import get_claude_task_analyzer
import logging

logger = logging.getLogger(__name__)
smart_scheduling_bp = Blueprint('smart_scheduling', __name__)

# Initialize service
smart_service = SmartSchedulingService()


@smart_scheduling_bp.route('/schedule/daily-routine', methods=['POST'])
def run_daily_routine():
    """
    Run the complete daily scheduling routine
    
    This is the main YOLO.md endpoint that:
    - Handles recurring tasks
    - Creates meal prep tasks  
    - Updates weather forecasts
    - Performs smart bulk assignment
    """
    try:
        logger.info("Starting daily scheduling routine...")
        
        results = smart_service.daily_scheduling_routine()
        
        logger.info(f"Daily routine completed: {results}")
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'routine': 'daily_scheduling',
            'results': results,
            'message': 'Daily scheduling routine completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Daily routine failed: {e}")
        return jsonify({
            'success': False,
            'error': f"Daily routine failed: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500


@smart_scheduling_bp.route('/projects/<project_id>/smart-assign', methods=['POST'])
def smart_assign_project(project_id):
    """
    Smart assignment for all tasks in a project
    
    Assigns tasks respecting:
    - Project dependencies
    - Phase deadlines
    - Event conflicts
    - Priority scoring
    """
    try:
        logger.info(f"Starting smart project assignment for project {project_id}")
        
        # Verify project exists
        project = Project.query.get(project_id)
        if not project:
            return jsonify({
                'success': False,
                'error': f'Project {project_id} not found'
            }), 404
        
        result = smart_service.assignment_service.assign_project_tasks_smart(project_id)
        
        logger.info(f"Project assignment completed: {result}")
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'project_title': project.title,
            'assignment_result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Smart project assignment failed for {project_id}: {e}")
        return jsonify({
            'success': False,
            'project_id': project_id,
            'error': f"Smart assignment failed: {str(e)}"
        }), 500


@smart_scheduling_bp.route('/tasks/analyze-with-context', methods=['POST'])
def analyze_task_with_context():
    """
    Analyze task with comprehensive project/meal/initiative context
    
    Body should contain:
    - title: Task title
    - project_id (optional): Project context
    - phase_id (optional): Phase context  
    - meal_id (optional): Meal context
    - description (optional): Task description
    """
    try:
        data = request.json or {}
        
        if not data.get('title'):
            return jsonify({
                'success': False,
                'error': 'Task title is required'
            }), 400
        
        title = data['title']
        project_id = data.get('project_id')
        phase_id = data.get('phase_id')
        meal_id = data.get('meal_id')
        
        logger.info(f"Analyzing task with context: {title}")
        
        # Build context dictionary
        context = {}
        
        if project_id:
            project = Project.query.get(project_id)
            if project:
                context['project'] = project.to_dict()
            else:
                logger.warning(f"Project {project_id} not found")
        
        if phase_id:
            phase = ProjectPhase.query.get(phase_id)
            if phase:
                context['phase'] = phase.to_dict()
            else:
                logger.warning(f"Phase {phase_id} not found")
        
        if meal_id:
            from models import Meal
            meal = Meal.query.get(meal_id)
            if meal:
                context['meal'] = meal.to_dict()
            else:
                logger.warning(f"Meal {meal_id} not found")
        
        # Create task data for analysis
        task_data = {
            'title': title,
            'description': data.get('description', ''),
            'duration': data.get('duration', 60),
            'urgency': data.get('urgency', 5),
            'project_id': project_id,
            'phase_id': phase_id,
            'meal_id': meal_id
        }
        
        # Perform Claude analysis with context
        analyzer = get_claude_task_analyzer()
        analysis = analyzer.analyze_task_comprehensive(task_data, context)
        
        logger.info(f"Context analysis completed for: {title}")
        
        return jsonify({
            'success': True,
            'task_title': title,
            'context': context,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Context analysis failed: {e}")
        return jsonify({
            'success': False,
            'error': f"Context analysis failed: {str(e)}"
        }), 500


@smart_scheduling_bp.route('/tasks/<task_id>/suggest-breakdown', methods=['GET'])
def suggest_task_breakdown(task_id):
    """
    Get Claude's suggestion for breaking down a large task
    
    Returns suggestions for chunking tasks > 90 minutes
    """
    try:
        task = Task.query.get_or_404(task_id)
        
        if not task.is_divisible or task.duration <= 90:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'task_title': task.title,
                'breakdown_needed': False,
                'suggestions': [{
                    'title': task.title, 
                    'duration': task.duration,
                    'order': 1
                }],
                'message': 'Task does not require breakdown'
            })
        
        logger.info(f"Generating breakdown suggestions for task {task_id}: {task.title}")
        
        analyzer = get_claude_task_analyzer()
        suggestions = analyzer.claude_client.suggest_task_breakdown(
            task.title, 
            task.duration
        ) if analyzer.is_claude_available else []
        
        # Fallback if Claude not available
        if not suggestions and task.duration > 90:
            chunks = task.duration // 60
            suggestions = [
                {
                    'title': f"{task.title} - Part {i+1}", 
                    'duration': 60,
                    'order': i+1
                }
                for i in range(chunks)
            ]
        
        logger.info(f"Generated {len(suggestions)} breakdown suggestions")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'task_title': task.title,
            'total_duration': task.duration,
            'breakdown_needed': True,
            'suggestions': suggestions,
            'ai_powered': analyzer.is_claude_available
        })
        
    except Exception as e:
        logger.error(f"Task breakdown suggestion failed for {task_id}: {e}")
        return jsonify({
            'success': False,
            'task_id': task_id,
            'error': f"Breakdown suggestion failed: {str(e)}"
        }), 500


@smart_scheduling_bp.route('/schedule/optimize-week', methods=['POST'])
def optimize_week():
    """
    Optimize the entire week's schedule
    
    Optional body parameters:
    - incremental: true/false (default: true)
    - start_date: YYYY-MM-DD (default: today)
    - days: number of days to optimize (default: 7)
    """
    try:
        data = request.json or {}
        
        incremental = data.get('incremental', True)
        start_date_str = data.get('start_date')
        days = data.get('days', 7)
        
        # Parse start date
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str).date()
        else:
            start_date = date.today()
        
        end_date = start_date + timedelta(days=days)
        
        logger.info(f"Optimizing schedule from {start_date} to {end_date} (incremental: {incremental})")
        
        # Run smart assignment for the period
        result = smart_service.smart_assign_all_tasks(incremental=incremental)
        
        # Get assignments by day for the period
        assignments_by_day = {}
        
        if result.get('assignments'):
            for assignment in result['assignments']:
                try:
                    pool = TimePool.query.get(assignment.get('pool_id'))
                    if pool and start_date <= pool.pool_date <= end_date:
                        day = pool.pool_date.isoformat()
                        if day not in assignments_by_day:
                            assignments_by_day[day] = []
                        assignments_by_day[day].append(assignment)
                except Exception as e:
                    logger.warning(f"Error processing assignment: {e}")
        
        logger.info(f"Week optimization completed: {len(assignments_by_day)} days with assignments")
        
        return jsonify({
            'success': True,
            'optimization_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'incremental': incremental,
            'total_assignments': result.get('assignments_made', 0),
            'assignments_by_day': assignments_by_day,
            'optimization_summary': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Week optimization failed: {e}")
        return jsonify({
            'success': False,
            'error': f"Week optimization failed: {str(e)}"
        }), 500


@smart_scheduling_bp.route('/meals/prepare-tasks', methods=['POST'])
def prepare_meal_tasks():
    """
    Create tasks for upcoming meal preparation
    
    Optional body parameters:
    - days_ahead: Number of days to look ahead (default: 3)
    """
    try:
        data = request.json or {}
        days_ahead = data.get('days_ahead', 3)
        
        logger.info(f"Preparing meal tasks for next {days_ahead} days")
        
        result = smart_service.assignment_service.prepare_meal_tasks(days_ahead)
        
        logger.info(f"Meal task preparation completed: {result}")
        
        return jsonify({
            'success': True,
            'days_ahead': days_ahead,
            'meal_preparation_result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Meal task preparation failed: {e}")
        return jsonify({
            'success': False,
            'error': f"Meal task preparation failed: {str(e)}"
        }), 500


@smart_scheduling_bp.route('/schedule/status', methods=['GET'])
def get_smart_scheduling_status():
    """
    Get smart scheduling service status and capabilities
    """
    try:
        analyzer = get_claude_task_analyzer()
        
        # Check if required services are available
        status = {
            'service_available': True,
            'claude_analyzer_available': analyzer.is_claude_available,
            'smart_scheduling_service_initialized': smart_service is not None,
            'capabilities': [
                'daily_routine',
                'project_smart_assignment',
                'context_aware_analysis',
                'task_breakdown_suggestions',
                'week_optimization',
                'meal_task_preparation'
            ],
            'endpoints': [
                '/api/schedule/daily-routine',
                '/api/projects/{id}/smart-assign',
                '/api/tasks/analyze-with-context',
                '/api/tasks/{id}/suggest-breakdown',
                '/api/schedule/optimize-week',
                '/api/meals/prepare-tasks'
            ],
            'yolo_implementation_status': {
                'phase_1_services': 'implemented',
                'phase_2_api_routes': 'implemented',
                'phase_3_database': 'implemented'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            'service_available': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@smart_scheduling_bp.route('/recurring-tasks/process', methods=['POST'])
def process_recurring_tasks():
    """
    Process recurring tasks that need regeneration
    
    Part of daily routine but can be called independently
    """
    try:
        logger.info("Processing recurring tasks...")
        
        result = smart_service.assignment_service.handle_recurring_tasks()
        
        logger.info(f"Recurring task processing completed: {result}")
        
        return jsonify({
            'success': True,
            'recurring_task_result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Recurring task processing failed: {e}")
        return jsonify({
            'success': False,
            'error': f"Recurring task processing failed: {str(e)}"
        }), 500