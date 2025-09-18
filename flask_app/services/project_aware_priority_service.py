# project_aware_priority_service.py - Advanced Priority Scoring Service for TaskMaster YOLO
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Task, Project, ProjectPhase, Initiative, Meal, TaskAssignment
import json

logger = logging.getLogger(__name__)

# Priority scoring constants
MAX_TIME_CRITICALITY = 300
MAX_PROJECT_URGENCY = 200
MAX_DEPENDENCY_IMPACT = 200
MAX_PROGRESS_MOMENTUM = 150
MAX_RECURRING_TIMING = 100
MAX_MEAL_TIMING = 150
MAX_QUICK_WINS = 50

class ProjectAwarePriorityService:
    """Priority scoring that understands project context and dependencies"""
    
    def __init__(self):
        self.logger = logger
    
    def calculate_priority_score(self, task: Dict, all_tasks: List[Dict] = None) -> float:
        """
        Enhanced scoring (0-1000 points):
        - Time criticality: 0-300 points
        - Project urgency: 0-200 points (phase deadlines, project priority)
        - Dependency impact: 0-200 points (blocking other tasks)
        - Progress momentum: 0-150 points (continue active projects)
        - Recurring task timing: 0-100 points
        - Meal timing: 0-150 points (serve time proximity)
        - Quick wins: 0-50 points
        """
        try:
            total_score = 0.0
            
            # Component scores
            time_score = self._calculate_time_criticality(task)
            project_score = self._calculate_project_urgency(task)
            dependency_score = self._calculate_dependency_impact(task, all_tasks or [])
            momentum_score = self._calculate_progress_momentum(task)
            recurring_score = self._calculate_recurring_timing(task)
            meal_score = self._calculate_meal_timing(task)
            quick_win_score = self._calculate_quick_wins(task)
            
            total_score = (time_score + project_score + dependency_score + 
                          momentum_score + recurring_score + meal_score + quick_win_score)
            
            self.logger.debug(f"Priority breakdown for task '{task.get('title', 'Unknown')}': "
                            f"Time={time_score:.1f}, Project={project_score:.1f}, "
                            f"Dependency={dependency_score:.1f}, Momentum={momentum_score:.1f}, "
                            f"Recurring={recurring_score:.1f}, Meal={meal_score:.1f}, "
                            f"QuickWin={quick_win_score:.1f}, Total={total_score:.1f}")
            
            return max(0.0, min(1000.0, total_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating priority score for task {task.get('id', 'unknown')}: {e}")
            return 100.0  # Default fallback score
    
    def _calculate_time_criticality(self, task: Dict) -> float:
        """Time criticality scoring (0-300 points)"""
        score = 0.0
        now = datetime.now()
        today = now.date()
        
        try:
            # Due date scoring
            if task.get('due_date'):
                due_date = self._parse_date(task['due_date'])
                if due_date:
                    days_until_due = (due_date - today).days
                    
                    if days_until_due < 0:
                        # Overdue - escalating penalty
                        overdue_days = abs(days_until_due)
                        score += min(250, 200 + (overdue_days * 10))
                    elif days_until_due == 0:
                        # Due today
                        score += 150
                        # Time-specific boost for due time
                        if task.get('due_time'):
                            try:
                                due_time = datetime.strptime(task['due_time'], '%H:%M:%S').time()
                                due_datetime = datetime.combine(due_date, due_time)
                                hours_until = (due_datetime - now).total_seconds() / 3600
                                if 0 <= hours_until <= 2:
                                    score += 50  # Due within 2 hours
                                elif hours_until <= 6:
                                    score += 30  # Due within 6 hours
                            except:
                                pass
                    elif days_until_due == 1:
                        score += 100  # Due tomorrow
                    elif days_until_due <= 3:
                        score += 75   # Due within 3 days
                    elif days_until_due <= 7:
                        score += 50   # Due within week
                    else:
                        score += 20   # Future due date
            
            # Urgency scaling
            urgency = task.get('urgency', 5)
            if isinstance(urgency, (int, float)) and urgency > 5:
                score += min(50, (urgency - 5) * 10)
            
            return min(MAX_TIME_CRITICALITY, score)
            
        except Exception as e:
            self.logger.warning(f"Error calculating time criticality: {e}")
            return 50.0
    
    def _calculate_project_urgency(self, task: Dict) -> float:
        """Project context scoring (0-200 points)"""
        score = 0.0
        
        try:
            # Project priority boost
            if task.get('project_id'):
                project = self._get_project_context(task['project_id'])
                if project:
                    # Project priority mapping
                    priority_map = {'HIGH': 80, 'MEDIUM': 50, 'LOW': 20}
                    priority_score = priority_map.get(project.get('priority', 'MEDIUM'), 50)
                    score += priority_score
                    
                    # Project status boost
                    if project.get('status') == 'ACTIVE':
                        score += 30
                    
                    # Project deadline proximity
                    if project.get('estimated_end_date'):
                        end_date = self._parse_date(project['estimated_end_date'])
                        if end_date:
                            days_until_end = (end_date - date.today()).days
                            if days_until_end <= 7:
                                score += 40  # Project ending soon
                            elif days_until_end <= 30:
                                score += 20  # Project ending this month
            
            # Phase urgency
            if task.get('phase_id'):
                phase = self._get_phase_context(task['phase_id'])
                if phase:
                    if phase.get('status') == 'ACTIVE':
                        score += 25
                    
                    # Phase deadline proximity
                    if phase.get('estimated_end_date'):
                        end_date = self._parse_date(phase['estimated_end_date'])
                        if end_date:
                            days_until_end = (end_date - date.today()).days
                            if days_until_end <= 3:
                                score += 50  # Phase ending very soon
                            elif days_until_end <= 7:
                                score += 30  # Phase ending soon
            
            # Initiative context
            if task.get('initiative_id'):
                initiative = self._get_initiative_context(task['initiative_id'])
                if initiative and initiative.get('status') == 'ACTIVE':
                    score += 15
            
            return min(MAX_PROJECT_URGENCY, score)
            
        except Exception as e:
            self.logger.warning(f"Error calculating project urgency: {e}")
            return 30.0
    
    def _calculate_dependency_impact(self, task: Dict, all_tasks: List[Dict]) -> float:
        """Dependency impact scoring (0-200 points)"""
        score = 0.0
        
        try:
            task_id = task.get('id')
            if not task_id:
                return 0.0
            
            # Count how many tasks this task blocks
            blocked_tasks = []
            for other_task in all_tasks:
                depends_on = other_task.get('depends_on_task_ids')
                if depends_on:
                    try:
                        if isinstance(depends_on, str):
                            deps = json.loads(depends_on) if depends_on != 'null' else []
                        else:
                            deps = depends_on or []
                        
                        if task_id in deps:
                            blocked_tasks.append(other_task)
                    except:
                        pass
            
            # Base scoring for blocking tasks
            if blocked_tasks:
                base_score = min(100, len(blocked_tasks) * 25)
                score += base_score
                
                # Additional boost for blocking high-priority tasks
                for blocked_task in blocked_tasks:
                    blocked_urgency = blocked_task.get('urgency', 5)
                    if blocked_urgency >= 8:
                        score += 30  # Blocking urgent task
                    elif blocked_urgency >= 6:
                        score += 15  # Blocking medium-priority task
                    
                    # Boost for blocking overdue tasks
                    if blocked_task.get('due_date'):
                        due_date = self._parse_date(blocked_task['due_date'])
                        if due_date and due_date < date.today():
                            score += 40  # Blocking overdue task
            
            # Check if this task is blocked (penalty)
            depends_on = task.get('depends_on_task_ids')
            if depends_on:
                try:
                    if isinstance(depends_on, str):
                        deps = json.loads(depends_on) if depends_on != 'null' else []
                    else:
                        deps = depends_on or []
                    
                    if deps:
                        # Check if dependencies are completed
                        incomplete_deps = []
                        for dep_id in deps:
                            dep_task = next((t for t in all_tasks if t.get('id') == dep_id), None)
                            if dep_task and not dep_task.get('completed', False):
                                incomplete_deps.append(dep_task)
                        
                        if incomplete_deps:
                            score -= 50  # Penalty for being blocked
                except:
                    pass
            
            return min(MAX_DEPENDENCY_IMPACT, score)
            
        except Exception as e:
            self.logger.warning(f"Error calculating dependency impact: {e}")
            return 25.0
    
    def _calculate_progress_momentum(self, task: Dict) -> float:
        """Progress momentum scoring (0-150 points)"""
        score = 0.0
        
        try:
            # Partial completion boost
            partial_minutes = task.get('partial_completion_minutes', 0)
            duration = task.get('duration', 60)
            
            if partial_minutes and partial_minutes > 0:
                completion_ratio = partial_minutes / duration
                if completion_ratio >= 0.75:
                    score += 80  # Nearly done
                elif completion_ratio >= 0.5:
                    score += 60  # Half done
                elif completion_ratio >= 0.25:
                    score += 40  # Quarter done
                else:
                    score += 20  # Some progress
            
            # Recent work boost
            if task.get('last_completed_at'):
                try:
                    last_work = self._parse_datetime(task['last_completed_at'])
                    if last_work:
                        hours_since = (datetime.now() - last_work).total_seconds() / 3600
                        if hours_since <= 24:
                            score += 30  # Worked on recently
                        elif hours_since <= 72:
                            score += 15  # Worked on this week
                except:
                    pass
            
            # Active project momentum
            if task.get('project_id'):
                project = self._get_project_context(task['project_id'])
                if project and project.get('status') == 'ACTIVE':
                    # Check if other tasks in project were worked on recently
                    score += 20  # Keep project momentum
            
            return min(MAX_PROGRESS_MOMENTUM, score)
            
        except Exception as e:
            self.logger.warning(f"Error calculating progress momentum: {e}")
            return 10.0
    
    def _calculate_recurring_timing(self, task: Dict) -> float:
        """Recurring task timing (0-100 points)"""
        score = 0.0
        
        try:
            if task.get('is_recurring') and task.get('recurrence_days'):
                recurrence_days = task.get('recurrence_days', 1)
                last_completed = task.get('last_completed_at')
                
                if last_completed:
                    last_date = self._parse_datetime(last_completed)
                    if last_date:
                        days_since = (datetime.now() - last_date).days
                        
                        if days_since >= recurrence_days:
                            # Overdue for recurrence
                            overdue_cycles = days_since // recurrence_days
                            score += min(80, 40 + (overdue_cycles * 20))
                        elif days_since >= (recurrence_days * 0.8):
                            # Almost time for next occurrence
                            score += 60
                        elif days_since >= (recurrence_days * 0.5):
                            # Halfway to next occurrence
                            score += 30
                else:
                    # Never completed recurring task
                    score += 70
                
                # Daily tasks get slight boost
                if recurrence_days == 1:
                    score += 20
            
            return min(MAX_RECURRING_TIMING, score)
            
        except Exception as e:
            self.logger.warning(f"Error calculating recurring timing: {e}")
            return 0.0
    
    def _calculate_meal_timing(self, task: Dict) -> float:
        """Meal preparation timing (0-150 points)"""
        score = 0.0
        
        try:
            if task.get('meal_id'):
                meal = self._get_meal_context(task['meal_id'])
                if meal and meal.get('serve_time'):
                    serve_time = self._parse_datetime(meal['serve_time'])
                    if serve_time:
                        now = datetime.now()
                        hours_until_serve = (serve_time - now).total_seconds() / 3600
                        
                        # Task title analysis for prep timing
                        title_lower = task.get('title', '').lower()
                        
                        if 'prep' in title_lower or 'prepare' in title_lower:
                            # Prep tasks - need to be done earlier
                            if 2 <= hours_until_serve <= 4:
                                score += 100  # Perfect prep timing
                            elif 1 <= hours_until_serve <= 6:
                                score += 80   # Good prep timing
                            elif hours_until_serve <= 1:
                                score += 120  # Urgent prep needed
                        
                        elif 'cook' in title_lower or 'make' in title_lower:
                            # Cooking tasks - closer to serve time
                            if 0.5 <= hours_until_serve <= 2:
                                score += 120  # Perfect cooking timing
                            elif hours_until_serve <= 0.5:
                                score += 140  # Urgent cooking needed
                            elif hours_until_serve <= 3:
                                score += 90   # Good cooking timing
                        
                        else:
                            # General meal task
                            if hours_until_serve <= 1:
                                score += 100  # Urgent meal task
                            elif hours_until_serve <= 3:
                                score += 70   # Important meal task
                        
                        # Penalty for overdue meal tasks
                        if hours_until_serve < 0:
                            score += 150  # Maximum urgency for overdue meals
            
            return min(MAX_MEAL_TIMING, score)
            
        except Exception as e:
            self.logger.warning(f"Error calculating meal timing: {e}")
            return 0.0
    
    def _calculate_quick_wins(self, task: Dict) -> float:
        """Quick wins scoring (0-50 points)"""
        score = 0.0
        
        try:
            duration = task.get('duration', 60)
            
            # Duration-based quick win scoring
            if duration <= 15:
                score += 40  # Very quick task
            elif duration <= 30:
                score += 30  # Quick task
            elif duration <= 60:
                score += 20  # Medium-quick task
            
            # Easy tasks get boost
            urgency = task.get('urgency', 5)
            if urgency <= 3:
                score += 10  # Easy task
            
            return min(MAX_QUICK_WINS, score)
            
        except Exception as e:
            self.logger.warning(f"Error calculating quick wins: {e}")
            return 5.0
    
    def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """Get full task context including relationships"""
        try:
            task = Task.query.get(task_id)
            if not task:
                return {}
            
            context = {
                'task': task.to_dict(),
                'project': None,
                'phase': None,
                'initiative': None,
                'meal': None,
                'assignments': [],
                'blocking_tasks': [],
                'blocked_by_tasks': []
            }
            
            # Get project context
            if task.project_id:
                context['project'] = self._get_project_context(task.project_id)
            
            # Get phase context
            if task.phase_id:
                context['phase'] = self._get_phase_context(task.phase_id)
            
            # Get initiative context
            if task.initiative_id:
                context['initiative'] = self._get_initiative_context(task.initiative_id)
            
            # Get meal context
            if task.meal_id:
                context['meal'] = self._get_meal_context(task.meal_id)
            
            # Get assignments
            assignments = TaskAssignment.query.filter_by(task_id=task_id).all()
            context['assignments'] = [a.to_dict() for a in assignments]
            
            # Get dependency relationships
            context.update(self._get_dependency_context(task_id))
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting task context for {task_id}: {e}")
            return {}
    
    def _get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project information"""
        try:
            project = Project.query.get(project_id)
            return project.to_dict() if project else None
        except:
            return None
    
    def _get_phase_context(self, phase_id: str) -> Optional[Dict[str, Any]]:
        """Get project phase information"""
        try:
            phase = ProjectPhase.query.get(phase_id)
            return phase.to_dict() if phase else None
        except:
            return None
    
    def _get_initiative_context(self, initiative_id: str) -> Optional[Dict[str, Any]]:
        """Get initiative information"""
        try:
            initiative = Initiative.query.get(initiative_id)
            return initiative.to_dict() if initiative else None
        except:
            return None
    
    def _get_meal_context(self, meal_id: str) -> Optional[Dict[str, Any]]:
        """Get meal information"""
        try:
            meal = Meal.query.get(meal_id)
            return meal.to_dict() if meal else None
        except:
            return None
    
    def _get_dependency_context(self, task_id: str) -> Dict[str, Any]:
        """Get tasks that this task blocks and is blocked by"""
        try:
            # Find tasks this task blocks
            blocking_tasks = Task.query.filter(
                Task.depends_on_task_ids.contains(f'"{task_id}"')
            ).all()
            
            # Find tasks that block this task
            task = Task.query.get(task_id)
            blocked_by_tasks = []
            if task and task.depends_on_task_ids:
                try:
                    deps = json.loads(task.depends_on_task_ids) if task.depends_on_task_ids != 'null' else []
                    if deps:
                        blocked_by_tasks = Task.query.filter(Task.id.in_(deps)).all()
                except:
                    pass
            
            return {
                'blocking_tasks': [t.to_dict() for t in blocking_tasks],
                'blocked_by_tasks': [t.to_dict() for t in blocked_by_tasks]
            }
            
        except Exception as e:
            self.logger.warning(f"Error getting dependency context: {e}")
            return {'blocking_tasks': [], 'blocked_by_tasks': []}
    
    def _parse_date(self, date_str: Any) -> Optional[date]:
        """Parse date from various formats"""
        try:
            if isinstance(date_str, date):
                return date_str
            elif isinstance(date_str, datetime):
                return date_str.date()
            elif isinstance(date_str, str):
                # Try ISO format first
                try:
                    return datetime.fromisoformat(date_str.replace('Z', '')).date()
                except:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            pass
        return None
    
    def _parse_datetime(self, dt_str: Any) -> Optional[datetime]:
        """Parse datetime from various formats"""
        try:
            if isinstance(dt_str, datetime):
                return dt_str
            elif isinstance(dt_str, str):
                return datetime.fromisoformat(dt_str.replace('Z', ''))
        except:
            pass
        return None

# Global service instance
_priority_service: Optional[ProjectAwarePriorityService] = None

def get_project_aware_priority_service() -> ProjectAwarePriorityService:
    """Get the global priority service instance"""
    global _priority_service
    if not _priority_service:
        _priority_service = ProjectAwarePriorityService()
    return _priority_service