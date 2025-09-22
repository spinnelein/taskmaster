"""
Claude Analysis API Routes

Handles AI-powered analysis endpoints including task analysis,
complexity assessment, and optimization suggestions.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from models import db, Task
from services.claude_task_analyzer import get_claude_task_analyzer
import logging

logger = logging.getLogger(__name__)
analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/tasks/<task_id>/claude-analysis', methods=['GET'])
def get_task_claude_analysis(task_id):
    """Get comprehensive Claude AI analysis for a specific task"""
    try:
        # Get the task
        task = Task.query.get_or_404(task_id)
        task_dict = task.to_dict()
        
        # Get optional parameters
        include_context = request.args.get('include_context', 'true').lower() == 'true'
        save_to_db = request.args.get('save_to_db', 'false').lower() == 'true'
        context = None
        
        if include_context:
            # Get project/initiative context
            analyzer = get_claude_task_analyzer()
            context = analyzer.get_task_context(task_id)
        
        # Perform analysis
        analyzer = get_claude_task_analyzer()
        analysis = analyzer.analyze_task_comprehensive(task_dict, context, save_to_db=save_to_db)
        
        response_data = {
            'success': True,
            'task_id': task_id,
            'task_title': task_dict.get('title', 'Unknown'),
            'analysis': analysis,
            'context_included': include_context,
            'saved_to_db': save_to_db
        }
        
        # If saved to DB, include YOLO field values
        if save_to_db:
            # Refresh task from DB to get updated YOLO fields
            db.session.refresh(task)
            response_data['yolo_fields'] = {
                'cognitive_load': task.cognitive_load,
                'energy_level': task.energy_level,
                'last_analyzed': task.last_analyzed.isoformat() if task.last_analyzed else None,
                'ai_analysis_length': len(task.ai_analysis) if task.ai_analysis else 0
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error analyzing task {task_id} with Claude: {e}")
        return jsonify({
            'success': False,
            'error': f"Task analysis failed: {str(e)}",
            'task_id': task_id
        }), 500


@analysis_bp.route('/tasks/claude-analysis/batch', methods=['POST'])
def batch_claude_analysis():
    """Perform Claude analysis on multiple tasks"""
    try:
        data = request.json or {}
        task_ids = data.get('task_ids', [])
        save_to_db = data.get('save_to_db', False)
        
        if not task_ids:
            return jsonify({'error': 'task_ids required'}), 400
        
        if len(task_ids) > 10:
            return jsonify({'error': 'Maximum 10 tasks per batch request'}), 400
        
        analyzer = get_claude_task_analyzer()
        results = []
        successful_saves = 0
        
        for task_id in task_ids:
            try:
                task = Task.query.get(task_id)
                if task:
                    task_dict = task.to_dict()
                    analysis = analyzer.analyze_task_comprehensive(task_dict, save_to_db=save_to_db)
                    
                    result_data = {
                        'task_id': task_id,
                        'task_title': task_dict.get('title', 'Unknown'),
                        'analysis': analysis,
                        'success': True,
                        'saved_to_db': save_to_db
                    }
                    
                    # If saved to DB, include YOLO field values
                    if save_to_db:
                        db.session.refresh(task)
                        result_data['yolo_fields'] = {
                            'cognitive_load': task.cognitive_load,
                            'energy_level': task.energy_level,
                            'last_analyzed': task.last_analyzed.isoformat() if task.last_analyzed else None
                        }
                        successful_saves += 1
                    
                    results.append(result_data)
                else:
                    results.append({
                        'task_id': task_id,
                        'error': 'Task not found',
                        'success': False,
                        'saved_to_db': False
                    })
            except Exception as e:
                results.append({
                    'task_id': task_id,
                    'error': str(e),
                    'success': False,
                    'saved_to_db': False
                })
        
        successful_analyses = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'batch_size': len(task_ids),
            'successful_analyses': successful_analyses,
            'successful_saves': successful_saves if save_to_db else 0,
            'results': results,
            'saved_to_db': save_to_db
        })
        
    except Exception as e:
        logger.error(f"Error in batch Claude analysis: {e}")
        return jsonify({
            'success': False,
            'error': f"Batch analysis failed: {str(e)}"
        }), 500


@analysis_bp.route('/projects/<project_id>/claude-analysis', methods=['GET'])
def get_project_claude_analysis(project_id):
    """Get Claude analysis for all tasks in a project"""
    try:
        analyzer = get_claude_task_analyzer()
        result = analyzer.analyze_project_tasks(project_id)
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'analysis': result
        })
        
    except Exception as e:
        logger.error(f"Error analyzing project {project_id} with Claude: {e}")
        return jsonify({
            'success': False,
            'error': f"Project analysis failed: {str(e)}",
            'project_id': project_id
        }), 500


@analysis_bp.route('/claude-analysis/status', methods=['GET'])
def get_claude_analysis_status():
    """Get Claude analysis service status and capabilities"""
    try:
        analyzer = get_claude_task_analyzer()
        
        # Basic health check
        status = {
            'service_available': True,
            'analyzer_initialized': analyzer is not None,
            'capabilities': [
                'task_analysis',
                'project_analysis',
                'complexity_assessment',
                'optimization_suggestions',
                'batch_processing'
            ],
            'limits': {
                'max_batch_size': 10,
                'max_analysis_length': 4000
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error checking Claude analysis status: {e}")
        return jsonify({
            'service_available': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@analysis_bp.route('/tasks/<task_id>/suggestions', methods=['GET'])
def get_task_optimization_suggestions(task_id):
    """Get optimization suggestions for a specific task"""
    try:
        task = Task.query.get_or_404(task_id)
        task_dict = task.to_dict()
        
        analyzer = get_claude_task_analyzer()
        suggestions = analyzer.get_optimization_suggestions(task_dict)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'task_title': task_dict.get('title', 'Unknown'),
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error getting suggestions for task {task_id}: {e}")
        return jsonify({
            'success': False,
            'error': f"Failed to get suggestions: {str(e)}",
            'task_id': task_id
        }), 500


@analysis_bp.route('/claude-analysis/complexity-assessment', methods=['POST'])
def assess_task_complexity():
    """Assess complexity of a task or set of tasks"""
    try:
        data = request.json or {}
        
        if 'task_id' in data:
            # Single task complexity assessment
            task = Task.query.get_or_404(data['task_id'])
            task_dict = task.to_dict()
            
            analyzer = get_claude_task_analyzer()
            complexity = analyzer.assess_task_complexity(task_dict)
            
            return jsonify({
                'success': True,
                'assessment_type': 'single_task',
                'task_id': data['task_id'],
                'complexity': complexity
            })
            
        elif 'tasks' in data:
            # Multiple tasks complexity assessment
            tasks_data = data['tasks']
            
            analyzer = get_claude_task_analyzer()
            assessments = []
            
            for task_data in tasks_data:
                complexity = analyzer.assess_task_complexity(task_data)
                assessments.append({
                    'task_data': task_data,
                    'complexity': complexity
                })
            
            return jsonify({
                'success': True,
                'assessment_type': 'multiple_tasks',
                'assessments': assessments
            })
            
        else:
            return jsonify({
                'success': False,
                'error': 'Either task_id or tasks array is required'
            }), 400
            
    except Exception as e:
        logger.error(f"Error assessing task complexity: {e}")
        return jsonify({
            'success': False,
            'error': f"Complexity assessment failed: {str(e)}"
        }), 500


@analysis_bp.route('/tasks/<task_id>/analyze-and-save', methods=['POST'])
def analyze_and_save_task(task_id):
    """
    Analyze task with Claude AI and automatically save results to database YOLO fields
    
    This is the CRITICAL missing functionality - analysis results are now persisted!
    """
    try:
        analyzer = get_claude_task_analyzer()
        result = analyzer.analyze_and_save_task(task_id)
        
        if result['success']:
            logger.info(f"Successfully analyzed and saved task {task_id} to database")
            return jsonify({
                'success': True,
                'task_id': task_id,
                'task_title': result.get('task_title', 'Unknown'),
                'analysis': result['analysis'],
                'saved_to_db': result['saved_to_db'],
                'yolo_fields': result['yolo_fields'],
                'message': 'Task analyzed and saved to database YOLO fields'
            })
        else:
            logger.error(f"Failed to analyze and save task {task_id}: {result.get('error')}")
            return jsonify({
                'success': False,
                'task_id': task_id,
                'error': result.get('error', 'Unknown error'),
                'saved_to_db': False
            }), 500
            
    except Exception as e:
        logger.error(f"Error in analyze_and_save_task for {task_id}: {e}")
        return jsonify({
            'success': False,
            'task_id': task_id,
            'error': f"Analysis and save failed: {str(e)}",
            'saved_to_db': False
        }), 500


@analysis_bp.route('/tasks/batch-analyze-and-save', methods=['POST'])
def batch_analyze_and_save():
    """
    Batch analyze multiple tasks and save all results to database
    
    Useful for processing multiple tasks at once with database persistence
    """
    try:
        data = request.json or {}
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return jsonify({'error': 'task_ids required'}), 400
        
        if len(task_ids) > 10:
            return jsonify({'error': 'Maximum 10 tasks per batch request'}), 400
        
        analyzer = get_claude_task_analyzer()
        results = []
        successful_saves = 0
        
        for task_id in task_ids:
            try:
                result = analyzer.analyze_and_save_task(task_id)
                results.append(result)
                
                if result.get('success') and result.get('saved_to_db'):
                    successful_saves += 1
                    
            except Exception as e:
                results.append({
                    'success': False,
                    'task_id': task_id,
                    'error': str(e),
                    'saved_to_db': False
                })
        
        return jsonify({
            'success': True,
            'batch_size': len(task_ids),
            'successful_analyses': sum(1 for r in results if r.get('success')),
            'successful_saves': successful_saves,
            'results': results,
            'message': f'Processed {len(task_ids)} tasks, saved {successful_saves} to database'
        })
        
    except Exception as e:
        logger.error(f"Error in batch analyze and save: {e}")
        return jsonify({
            'success': False,
            'error': f"Batch analysis and save failed: {str(e)}"
        }), 500