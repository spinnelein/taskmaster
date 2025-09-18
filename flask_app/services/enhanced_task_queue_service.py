# enhanced_task_queue_service.py - Enhanced task queue service using ProjectAwarePriorityService
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Task, TaskAssignment
from .project_aware_priority_service import get_project_aware_priority_service

logger = logging.getLogger(__name__)

class EnhancedTaskQueueService:
    """Enhanced task queue service that uses ProjectAwarePriorityService for advanced scoring"""
    
    def __init__(self):
        self.priority_service = get_project_aware_priority_service()
    
    def get_enhanced_task_queue(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task queue with enhanced priority scoring"""
        try:
            # Get all incomplete tasks
            tasks = Task.query.filter(Task.is_completed == False).all()
            
            # Convert to dict format for priority service
            task_dicts = [task.to_dict() for task in tasks]
            
            # Calculate enhanced priority scores
            enhanced_queue = []
            for task_dict in task_dicts:
                # Get enhanced priority score
                enhanced_score = self.priority_service.calculate_priority_score(task_dict, task_dicts)
                
                # Get existing assignment info
                task_id = task_dict['id']
                active_assignments = TaskAssignment.query.filter_by(
                    task_id=task_id
                ).filter(TaskAssignment.status.in_(['assigned', 'started'])).all()
                
                total_assigned_minutes = sum(a.allocated_minutes for a in active_assignments)
                remaining_minutes = max(0, (task_dict.get('duration', 0) - total_assigned_minutes))
                
                # Enhance task dict with new scoring
                enhanced_task = task_dict.copy()
                enhanced_task.update({
                    'enhanced_priority_score': enhanced_score,
                    'is_assigned': len(active_assignments) > 0,
                    'is_fully_assigned': remaining_minutes <= 0,
                    'assigned_minutes': total_assigned_minutes,
                    'remaining_minutes': remaining_minutes,
                    'assignments': [a.to_dict() for a in active_assignments]
                })
                
                enhanced_queue.append(enhanced_task)
            
            # Sort by enhanced priority score (descending)
            enhanced_queue.sort(key=lambda x: x['enhanced_priority_score'], reverse=True)
            
            logger.info(f"Generated enhanced task queue with {len(enhanced_queue)} tasks")
            return enhanced_queue[:limit]
            
        except Exception as e:
            logger.error(f"Error generating enhanced task queue: {e}")
            return []
    
    def get_available_enhanced_queue(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get enhanced queue filtered to available tasks only"""
        try:
            full_queue = self.get_enhanced_task_queue(limit * 2)
            
            # Filter to tasks that aren't fully assigned and can be scheduled
            available_queue = []
            for task in full_queue:
                if not task['is_fully_assigned']:
                    # Additional availability checks could go here
                    # (snoozed status, dependencies, etc.)
                    available_queue.append(task)
            
            return available_queue[:limit]
            
        except Exception as e:
            logger.error(f"Error generating available enhanced queue: {e}")
            return []
    
    def get_task_context_analysis(self, task_id: str) -> Dict[str, Any]:
        """Get detailed context analysis for a specific task"""
        try:
            context = self.priority_service.get_task_context(task_id)
            
            if context and context.get('task'):
                task_dict = context['task']
                
                # Calculate priority breakdown
                enhanced_score = self.priority_service.calculate_priority_score(task_dict, [task_dict])
                
                # Add component scores for analysis
                components = {
                    'time_criticality': self.priority_service._calculate_time_criticality(task_dict),
                    'project_urgency': self.priority_service._calculate_project_urgency(task_dict),
                    'dependency_impact': self.priority_service._calculate_dependency_impact(task_dict, [task_dict]),
                    'progress_momentum': self.priority_service._calculate_progress_momentum(task_dict),
                    'recurring_timing': self.priority_service._calculate_recurring_timing(task_dict),
                    'meal_timing': self.priority_service._calculate_meal_timing(task_dict),
                    'quick_wins': self.priority_service._calculate_quick_wins(task_dict)
                }
                
                context['priority_analysis'] = {
                    'total_score': enhanced_score,
                    'components': components,
                    'top_factors': self._identify_top_priority_factors(components)
                }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting task context analysis for {task_id}: {e}")
            return {}
    
    def _identify_top_priority_factors(self, components: Dict[str, float]) -> List[str]:
        """Identify the top contributing factors to priority score"""
        sorted_components = sorted(components.items(), key=lambda x: x[1], reverse=True)
        
        top_factors = []
        for name, score in sorted_components:
            if score > 20:  # Only significant factors
                factor_name = name.replace('_', ' ').title()
                top_factors.append(f"{factor_name} ({score:.0f} pts)")
        
        return top_factors[:3]  # Top 3 factors
    
    def compare_task_priorities(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """Compare priority scores and factors for multiple tasks"""
        try:
            comparisons = []
            
            for task_id in task_ids:
                analysis = self.get_task_context_analysis(task_id)
                if analysis.get('task'):
                    comparison = {
                        'task_id': task_id,
                        'title': analysis['task'].get('title', 'Unknown'),
                        'total_score': analysis.get('priority_analysis', {}).get('total_score', 0),
                        'top_factors': analysis.get('priority_analysis', {}).get('top_factors', []),
                        'project': analysis.get('project', {}).get('title') if analysis.get('project') else None,
                        'due_date': analysis['task'].get('due_date'),
                        'urgency': analysis['task'].get('urgency', 5)
                    }
                    comparisons.append(comparison)
            
            # Sort by total score
            comparisons.sort(key=lambda x: x['total_score'], reverse=True)
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error comparing task priorities: {e}")
            return []

# Global enhanced service instance  
_enhanced_service: Optional[EnhancedTaskQueueService] = None

def get_enhanced_task_queue_service() -> EnhancedTaskQueueService:
    """Get the global enhanced task queue service instance"""
    global _enhanced_service
    if not _enhanced_service:
        _enhanced_service = EnhancedTaskQueueService()
    return _enhanced_service