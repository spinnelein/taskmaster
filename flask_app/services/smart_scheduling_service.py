# smart_scheduling_service.py - Master Smart Scheduling Service for TaskMaster YOLO
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
import sys
import os
import uuid
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Task, Event, TimePool, Project, ProjectPhase, Initiative, TaskAssignment
from services.project_aware_priority_service import get_project_aware_priority_service
from services.event_aware_assignment_service import get_event_aware_assignment_service
from services.claude_task_analyzer import get_claude_task_analyzer

logger = logging.getLogger(__name__)

class ConflictResolutionStrategy(Enum):
    """Strategies for resolving scheduling conflicts"""
    PRIORITY_FIRST = "priority_first"
    TIME_FLEXIBLE = "time_flexible"
    DEPENDENCY_DRIVEN = "dependency_driven"
    USER_PREFERENCE = "user_preference"
    OPTIMAL_BALANCE = "optimal_balance"

class SchedulingObjective(Enum):
    """Optimization objectives for scheduling"""
    MINIMIZE_COMPLETION_TIME = "minimize_completion_time"
    MAXIMIZE_URGENT_PRIORITY = "maximize_urgent_priority"
    OPTIMIZE_RESOURCE_USAGE = "optimize_resource_usage"
    REDUCE_CONTEXT_SWITCHING = "reduce_context_switching"
    RESPECT_ENERGY_PATTERNS = "respect_energy_patterns"

@dataclass
class SchedulingConstraint:
    """Represents a constraint in the scheduling system"""
    constraint_id: str
    constraint_type: str  # 'time', 'resource', 'dependency', 'preference'
    description: str
    hard_constraint: bool = True  # False for soft constraints
    weight: float = 1.0
    entities: List[str] = field(default_factory=list)  # IDs of affected tasks/events
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SchedulingResult:
    """Result of a scheduling operation"""
    success: bool
    schedule_id: str
    generated_at: datetime
    total_tasks: int
    scheduled_tasks: int
    unscheduled_tasks: int
    total_duration_hours: float
    optimization_score: float
    conflicts_resolved: int
    processing_time_seconds: float
    assignments: List[Dict[str, Any]] = field(default_factory=list)
    unscheduled: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

class SchedulingConstraintEngine:
    """Engine for managing and evaluating scheduling constraints"""
    
    def __init__(self):
        self.constraints: Dict[str, SchedulingConstraint] = {}
        self.constraint_evaluators = {
            'time': self._evaluate_time_constraint,
            'resource': self._evaluate_resource_constraint,
            'dependency': self._evaluate_dependency_constraint,
            'preference': self._evaluate_preference_constraint
        }
    
    def add_constraint(self, constraint: SchedulingConstraint) -> None:
        """Add a new constraint to the engine"""
        self.constraints[constraint.constraint_id] = constraint
        logger.debug(f"Added constraint: {constraint.constraint_type} - {constraint.description}")
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """Remove a constraint from the engine"""
        if constraint_id in self.constraints:
            del self.constraints[constraint_id]
            logger.debug(f"Removed constraint: {constraint_id}")
            return True
        return False
    
    def evaluate_assignment(self, task: Dict[str, Any], pool: TimePool) -> Tuple[bool, float, List[str]]:
        """
        Evaluate if a task can be assigned to a pool considering all constraints
        Returns: (can_assign, violation_score, violated_constraints)
        """
        can_assign = True
        total_violation_score = 0.0
        violated_constraints = []
        
        pool_start = datetime.combine(pool.pool_date, pool.start_time.time())
        pool_end = datetime.combine(pool.pool_date, pool.end_time.time())
        
        for constraint in self.constraints.values():
            if task['id'] in constraint.entities or 'all' in constraint.entities:
                evaluator = self.constraint_evaluators.get(constraint.constraint_type)
                if evaluator:
                    is_valid, violation_score = evaluator(constraint, task, pool, pool_start, pool_end)
                    
                    if not is_valid:
                        if constraint.hard_constraint:
                            can_assign = False
                        violated_constraints.append(constraint.constraint_id)
                        total_violation_score += violation_score * constraint.weight
        
        return can_assign, total_violation_score, violated_constraints
    
    def _evaluate_time_constraint(self, constraint: SchedulingConstraint, task: Dict[str, Any], 
                                pool: TimePool, pool_start: datetime, pool_end: datetime) -> Tuple[bool, float]:
        """Evaluate time-based constraints"""
        params = constraint.parameters
        
        # Check event conflicts
        if 'avoid_events' in params and params['avoid_events']:
            conflicting_events = Event.query.filter(
                Event.is_blocking == True,
                Event.start_time < pool_end,
                Event.end_time > pool_start
            ).count()
            
            if conflicting_events > 0:
                return False, 1.0
        
        # Check time range restrictions
        if 'allowed_hours' in params:
            allowed_start, allowed_end = params['allowed_hours']
            pool_hour = pool_start.hour
            
            if not (allowed_start <= pool_hour <= allowed_end):
                return False, 0.8
        
        # Check due date urgency
        if 'respect_due_dates' in params and params['respect_due_dates']:
            if task.get('due_date'):
                due_date = datetime.fromisoformat(task['due_date']) if isinstance(task['due_date'], str) else task['due_date']
                if isinstance(due_date, date):
                    due_date = datetime.combine(due_date, datetime.min.time())
                
                hours_until_due = (due_date - pool_start).total_seconds() / 3600
                if hours_until_due < 0:
                    return True, 0.9  # Overdue but not blocking
                elif hours_until_due < 24:
                    return True, 0.3  # Due soon, slight penalty
        
        return True, 0.0
    
    def _evaluate_resource_constraint(self, constraint: SchedulingConstraint, task: Dict[str, Any],
                                    pool: TimePool, pool_start: datetime, pool_end: datetime) -> Tuple[bool, float]:
        """Evaluate resource-based constraints"""
        params = constraint.parameters
        
        # Check pool capacity
        required_duration = task.get('duration', 30)
        if required_duration > pool.available_minutes:
            return False, 1.0
        
        # Check weather constraints for outdoor tasks
        if 'weather_dependent' in params and params['weather_dependent']:
            if any(keyword in task.get('title', '').lower() for keyword in ['outdoor', 'garden', 'yard']):
                # This would integrate with weather service
                # For now, basic check
                return True, 0.1
        
        return True, 0.0
    
    def _evaluate_dependency_constraint(self, constraint: SchedulingConstraint, task: Dict[str, Any],
                                      pool: TimePool, pool_start: datetime, pool_end: datetime) -> Tuple[bool, float]:
        """Evaluate dependency-based constraints"""
        # Check if task dependencies are satisfied
        depends_on = task.get('depends_on_task_ids')
        if depends_on:
            try:
                if isinstance(depends_on, str):
                    deps = json.loads(depends_on) if depends_on != 'null' else []
                else:
                    deps = depends_on or []
                
                if deps:
                    # Check if dependencies are completed or scheduled before this pool
                    for dep_id in deps:
                        dep_task = Task.query.get(dep_id)
                        if dep_task and not dep_task.is_completed:
                            # Check if dependency is scheduled before this pool
                            dep_assignments = TaskAssignment.query.filter_by(
                                task_id=dep_id
                            ).join(TimePool).filter(
                                TimePool.pool_date < pool.pool_date
                            ).first()
                            
                            if not dep_assignments:
                                return False, 1.0  # Dependency not satisfied
            except:
                pass
        
        return True, 0.0
    
    def _evaluate_preference_constraint(self, constraint: SchedulingConstraint, task: Dict[str, Any],
                                      pool: TimePool, pool_start: datetime, pool_end: datetime) -> Tuple[bool, float]:
        """Evaluate user preference constraints"""
        params = constraint.parameters
        
        # Check preferred time slots
        if 'preferred_times' in params:
            preferred_hour = params['preferred_times'].get(task.get('category', 'general'))
            if preferred_hour and abs(pool_start.hour - preferred_hour) > 2:
                return True, 0.3  # Soft constraint - not preferred but allowed
        
        # Check energy level patterns
        if 'energy_patterns' in params:
            energy_map = params['energy_patterns']
            hour = pool_start.hour
            if hour in energy_map:
                energy_level = energy_map[hour]
                task_complexity = task.get('urgency', 5)
                
                # High complexity tasks should be scheduled during high energy times
                if task_complexity >= 7 and energy_level < 0.6:
                    return True, 0.5  # Suboptimal but allowed
        
        return True, 0.0
    
    def get_constraints_summary(self) -> Dict[str, Any]:
        """Get summary of all active constraints"""
        summary = {
            'total_constraints': len(self.constraints),
            'hard_constraints': sum(1 for c in self.constraints.values() if c.hard_constraint),
            'soft_constraints': sum(1 for c in self.constraints.values() if not c.hard_constraint),
            'constraint_types': {}
        }
        
        for constraint in self.constraints.values():
            constraint_type = constraint.constraint_type
            if constraint_type not in summary['constraint_types']:
                summary['constraint_types'][constraint_type] = 0
            summary['constraint_types'][constraint_type] += 1
        
        return summary

class SmartSchedulingService:
    """Master scheduling service that coordinates all Phase 1 agents"""
    
    def __init__(self):
        self.logger = logger
        self.constraint_engine = SchedulingConstraintEngine()
        
        # Initialize Phase 1 services
        self.priority_service = get_project_aware_priority_service()
        self.assignment_service = get_event_aware_assignment_service()
        self.analyzer_service = get_claude_task_analyzer()
        
        # Configuration
        self.max_processing_time = 300  # 5 minutes max processing
        self.optimization_objectives = [
            SchedulingObjective.MAXIMIZE_URGENT_PRIORITY,
            SchedulingObjective.MINIMIZE_COMPLETION_TIME,
            SchedulingObjective.OPTIMIZE_RESOURCE_USAGE
        ]
        
        # Setup default constraints
        self._setup_default_constraints()
    
    def _setup_default_constraints(self) -> None:
        """Setup default scheduling constraints"""
        # Event conflict constraint
        event_constraint = SchedulingConstraint(
            constraint_id="avoid_blocking_events",
            constraint_type="time",
            description="Avoid scheduling tasks during blocking events",
            hard_constraint=True,
            weight=1.0,
            entities=["all"],
            parameters={"avoid_events": True}
        )
        self.constraint_engine.add_constraint(event_constraint)
        
        # Dependency constraint
        dep_constraint = SchedulingConstraint(
            constraint_id="respect_dependencies",
            constraint_type="dependency",
            description="Ensure task dependencies are satisfied before scheduling",
            hard_constraint=True,
            weight=1.0,
            entities=["all"]
        )
        self.constraint_engine.add_constraint(dep_constraint)
        
        # Working hours constraint
        working_hours_constraint = SchedulingConstraint(
            constraint_id="working_hours",
            constraint_type="time",
            description="Prefer scheduling during working hours",
            hard_constraint=False,
            weight=0.7,
            entities=["all"],
            parameters={"allowed_hours": (8, 18)}  # 8 AM to 6 PM
        )
        self.constraint_engine.add_constraint(working_hours_constraint)
        
        # Energy pattern constraint
        energy_constraint = SchedulingConstraint(
            constraint_id="energy_patterns",
            constraint_type="preference",
            description="Schedule complex tasks during high energy periods",
            hard_constraint=False,
            weight=0.5,
            entities=["all"],
            parameters={
                "energy_patterns": {
                    9: 0.9, 10: 1.0, 11: 0.9,  # High energy morning
                    14: 0.8, 15: 0.7, 16: 0.6,  # Afternoon dip
                    19: 0.7, 20: 0.6  # Evening moderate
                }
            }
        )
        self.constraint_engine.add_constraint(energy_constraint)
    
    def generate_optimal_schedule(
        self,
        start_date: date,
        end_date: date,
        task_filters: Dict[str, Any] = None,
        optimization_objectives: List[SchedulingObjective] = None,
        conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.OPTIMAL_BALANCE,
        clear_existing: bool = True
    ) -> SchedulingResult:
        """
        Generate optimal schedule using all Phase 1 services
        This is the main coordination method
        """
        start_time = time.time()
        schedule_id = str(uuid.uuid4())
        
        try:
            self.logger.info(f"Starting optimal schedule generation for {start_date} to {end_date}")
            
            # Step 1: Get available pools (event-aware)
            available_pools = self.assignment_service.get_available_pools_with_events(start_date, end_date)
            if not available_pools:
                return SchedulingResult(
                    success=False,
                    schedule_id=schedule_id,
                    generated_at=datetime.now(),
                    total_tasks=0,
                    scheduled_tasks=0,
                    unscheduled_tasks=0,
                    total_duration_hours=0.0,
                    optimization_score=0.0,
                    conflicts_resolved=0,
                    processing_time_seconds=time.time() - start_time,
                    recommendations=["No available time pools found in the specified date range"]
                )
            
            # Step 2: Get and prepare tasks
            tasks = self._get_schedulable_tasks(task_filters)
            if not tasks:
                return SchedulingResult(
                    success=True,
                    schedule_id=schedule_id,
                    generated_at=datetime.now(),
                    total_tasks=0,
                    scheduled_tasks=0,
                    unscheduled_tasks=0,
                    total_duration_hours=0.0,
                    optimization_score=1.0,
                    conflicts_resolved=0,
                    processing_time_seconds=time.time() - start_time,
                    recommendations=["No tasks require scheduling"]
                )
            
            # Step 3: Enhanced task analysis
            enriched_tasks = self._enrich_tasks_with_analysis(tasks)
            
            # Step 4: Priority scoring
            prioritized_tasks = self._calculate_priority_scores(enriched_tasks)
            
            # Step 5: Dependency ordering
            ordered_tasks = self._order_by_dependencies(prioritized_tasks)
            
            # Step 6: Clear existing assignments if requested
            if clear_existing:
                self._clear_existing_assignments(available_pools)
            
            # Step 7: Optimal assignment with constraint satisfaction
            assignments, unscheduled, conflicts = self._assign_optimally(
                ordered_tasks, available_pools, optimization_objectives or self.optimization_objectives
            )
            
            # Step 8: Conflict resolution
            resolved_conflicts = self._resolve_conflicts(conflicts, conflict_resolution)
            
            # Step 9: Calculate metrics and recommendations
            total_duration = sum(assignment['allocated_minutes'] for assignment in assignments) / 60.0
            optimization_score = self._calculate_optimization_score(assignments, prioritized_tasks)
            recommendations = self._generate_recommendations(assignments, unscheduled, conflicts)
            
            processing_time = time.time() - start_time
            
            result = SchedulingResult(
                success=True,
                schedule_id=schedule_id,
                generated_at=datetime.now(),
                total_tasks=len(tasks),
                scheduled_tasks=len(assignments),
                unscheduled_tasks=len(unscheduled),
                total_duration_hours=total_duration,
                optimization_score=optimization_score,
                conflicts_resolved=resolved_conflicts,
                processing_time_seconds=processing_time,
                assignments=assignments,
                unscheduled=unscheduled,
                conflicts=conflicts,
                recommendations=recommendations,
                performance_metrics={
                    'pools_evaluated': len(available_pools),
                    'constraint_checks': self._get_constraint_check_count(),
                    'ai_analyses_performed': self._get_ai_analysis_count(),
                    'priority_calculations': len(prioritized_tasks)
                }
            )
            
            self.logger.info(f"Schedule generation completed in {processing_time:.2f}s: "
                           f"{len(assignments)} tasks scheduled, {len(unscheduled)} unscheduled")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in optimal schedule generation: {e}")
            return SchedulingResult(
                success=False,
                schedule_id=schedule_id,
                generated_at=datetime.now(),
                total_tasks=len(tasks) if 'tasks' in locals() else 0,
                scheduled_tasks=0,
                unscheduled_tasks=0,
                total_duration_hours=0.0,
                optimization_score=0.0,
                conflicts_resolved=0,
                processing_time_seconds=time.time() - start_time,
                recommendations=[f"Schedule generation failed: {str(e)}"]
            )
    
    def _get_schedulable_tasks(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get tasks that can be scheduled"""
        query = Task.query.filter_by(is_completed=False)
        
        if filters:
            if 'project_id' in filters:
                query = query.filter_by(project_id=filters['project_id'])
            if 'urgency_min' in filters:
                query = query.filter(Task.urgency >= filters['urgency_min'])
            if 'max_duration' in filters:
                query = query.filter(Task.duration <= filters['max_duration'])
        
        tasks = query.all()
        return [task.to_dict() for task in tasks]
    
    def _enrich_tasks_with_analysis(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich tasks with AI analysis"""
        enriched_tasks = []
        
        for task in tasks:
            try:
                # Get comprehensive analysis
                analysis = self.analyzer_service.analyze_task_comprehensive(task)
                task['ai_analysis'] = analysis
                
                # Extract key insights for scheduling
                complexity = analysis.get('complexity_assessment', {})
                task['complexity_score'] = complexity.get('complexity_score', 5)
                task['estimated_duration'] = complexity.get('estimated_duration_minutes', task.get('duration', 30))
                
                dependencies = analysis.get('dependency_insights', {})
                task['has_dependencies'] = dependencies.get('has_dependencies', False)
                
                enriched_tasks.append(task)
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze task {task.get('id')}: {e}")
                enriched_tasks.append(task)  # Add without analysis
        
        return enriched_tasks
    
    def _calculate_priority_scores(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate priority scores for all tasks"""
        for task in tasks:
            try:
                priority_score = self.priority_service.calculate_priority_score(task, tasks)
                task['priority_score'] = priority_score
            except Exception as e:
                self.logger.warning(f"Failed to calculate priority for task {task.get('id')}: {e}")
                task['priority_score'] = 100.0  # Default fallback
        
        return sorted(tasks, key=lambda t: t['priority_score'], reverse=True)
    
    def _order_by_dependencies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Order tasks respecting dependencies using topological sort"""
        try:
            # Build dependency graph
            task_map = {task['id']: task for task in tasks}
            graph = {}
            in_degree = {}
            
            # Initialize graph
            for task in tasks:
                task_id = task['id']
                graph[task_id] = []
                in_degree[task_id] = 0
            
            # Build edges
            for task in tasks:
                task_id = task['id']
                depends_on = task.get('depends_on_task_ids', [])
                
                if isinstance(depends_on, str):
                    try:
                        depends_on = json.loads(depends_on) if depends_on != 'null' else []
                    except:
                        depends_on = []
                
                for dep_id in depends_on:
                    if dep_id in task_map:
                        graph[dep_id].append(task_id)
                        in_degree[task_id] += 1
            
            # Topological sort with priority
            ordered = []
            queue = [(task_id, task_map[task_id]['priority_score']) 
                    for task_id in in_degree if in_degree[task_id] == 0]
            queue.sort(key=lambda x: x[1], reverse=True)  # Sort by priority
            
            while queue:
                task_id, _ = queue.pop(0)
                ordered.append(task_map[task_id])
                
                # Update neighbors
                for neighbor in graph[task_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append((neighbor, task_map[neighbor]['priority_score']))
                        queue.sort(key=lambda x: x[1], reverse=True)
            
            # Add any remaining tasks (circular dependencies)
            remaining = [task for task in tasks if task not in ordered]
            ordered.extend(remaining)
            
            return ordered
            
        except Exception as e:
            self.logger.warning(f"Dependency ordering failed, using priority order: {e}")
            return tasks  # Fallback to priority order
    
    def _clear_existing_assignments(self, pools: List[TimePool]) -> None:
        """Clear existing assignments for the given pools"""
        try:
            pool_ids = [pool.id for pool in pools]
            TaskAssignment.query.filter(TaskAssignment.time_pool_id.in_(pool_ids)).delete()
            
            # Reset pool availability
            for pool in pools:
                pool.allocated_minutes = 0
                pool.available_minutes = pool.total_minutes
                pool.updated_at = datetime.utcnow()
            
            db.session.commit()
            self.logger.info(f"Cleared existing assignments for {len(pools)} pools")
            
        except Exception as e:
            self.logger.error(f"Error clearing assignments: {e}")
            db.session.rollback()
    
    def _assign_optimally(
        self, 
        tasks: List[Dict[str, Any]], 
        pools: List[TimePool],
        objectives: List[SchedulingObjective]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Assign tasks optimally considering all objectives"""
        assignments = []
        unscheduled = []
        conflicts = []
        
        # Create pool scoring matrix
        pool_scores = self._calculate_pool_scores(pools, objectives)
        
        for task in tasks:
            task_assigned = False
            best_assignment = None
            best_score = -1
            
            # Find best pool for this task
            for pool in pools:
                if pool.available_minutes <= 0:
                    continue
                
                # Check constraints
                can_assign, violation_score, violated_constraints = self.constraint_engine.evaluate_assignment(task, pool)
                
                if can_assign:
                    # Calculate assignment score
                    assignment_score = self._calculate_assignment_score(
                        task, pool, pool_scores.get(pool.id, 0.5), objectives
                    )
                    
                    # Adjust for constraint violations (soft constraints)
                    final_score = assignment_score - (violation_score * 0.3)
                    
                    if final_score > best_score:
                        best_score = final_score
                        allocation = min(task.get('estimated_duration', task.get('duration', 30)), pool.available_minutes)
                        best_assignment = {
                            'pool': pool,
                            'allocation': allocation,
                            'score': final_score,
                            'violated_constraints': violated_constraints
                        }
                
                elif violated_constraints:
                    conflicts.append({
                        'task_id': task['id'],
                        'task_title': task.get('title', 'Unknown'),
                        'pool_id': pool.id,
                        'violated_constraints': violated_constraints,
                        'violation_score': violation_score
                    })
            
            # Make the best assignment
            if best_assignment:
                pool = best_assignment['pool']
                allocation = best_assignment['allocation']
                
                # Create assignment
                success, message, assignment_dict = self.assignment_service.assign_task_to_pool(
                    task_id=task['id'],
                    time_pool_id=pool.id,
                    allocated_minutes=allocation,
                    assigned_by='smart_scheduler',
                    notes=f"Smart scheduling (score: {best_score:.2f})"
                )
                
                if success:
                    assignment_info = {
                        'task_id': task['id'],
                        'task_title': task.get('title', 'Unknown'),
                        'pool_id': pool.id,
                        'pool_date': pool.pool_date.isoformat(),
                        'pool_start': pool.start_time.isoformat(),
                        'allocated_minutes': allocation,
                        'assignment_score': best_score,
                        'priority_score': task.get('priority_score', 0),
                        'violated_soft_constraints': best_assignment['violated_constraints']
                    }
                    assignments.append(assignment_info)
                    
                    # Update pool availability
                    pool.available_minutes -= allocation
                    pool.allocated_minutes += allocation
                    task_assigned = True
            
            if not task_assigned:
                unscheduled.append({
                    'task_id': task['id'],
                    'task_title': task.get('title', 'Unknown'),
                    'duration': task.get('duration', 30),
                    'priority_score': task.get('priority_score', 0),
                    'reason': 'No suitable time pools available'
                })
        
        return assignments, unscheduled, conflicts
    
    def _calculate_pool_scores(self, pools: List[TimePool], objectives: List[SchedulingObjective]) -> Dict[str, float]:
        """Calculate base scores for pools based on objectives"""
        pool_scores = {}
        
        for pool in pools:
            score = 0.5  # Base score
            
            # Time-based scoring
            pool_hour = pool.start_time.hour
            
            if SchedulingObjective.RESPECT_ENERGY_PATTERNS in objectives:
                # Higher scores for high-energy times
                if 9 <= pool_hour <= 11:
                    score += 0.3
                elif 14 <= pool_hour <= 16:
                    score += 0.1
                elif 19 <= pool_hour <= 21:
                    score += 0.2
            
            if SchedulingObjective.OPTIMIZE_RESOURCE_USAGE in objectives:
                # Prefer larger pools for better utilization
                utilization_potential = pool.total_minutes / 120.0  # Normalize to 2-hour max
                score += min(0.2, utilization_potential * 0.2)
            
            pool_scores[pool.id] = min(1.0, score)
        
        return pool_scores
    
    def _calculate_assignment_score(
        self, 
        task: Dict[str, Any], 
        pool: TimePool, 
        pool_base_score: float,
        objectives: List[SchedulingObjective]
    ) -> float:
        """Calculate score for assigning a specific task to a specific pool"""
        score = pool_base_score
        
        # Priority boost
        if SchedulingObjective.MAXIMIZE_URGENT_PRIORITY in objectives:
            priority_score = task.get('priority_score', 100) / 1000.0  # Normalize
            score += priority_score * 0.4
        
        # Complexity matching
        complexity = task.get('complexity_score', 5)
        pool_hour = pool.start_time.hour
        
        # Match complex tasks to high-energy times
        if complexity >= 7 and 9 <= pool_hour <= 11:
            score += 0.2
        elif complexity <= 3 and (pool_hour <= 8 or pool_hour >= 17):
            score += 0.1
        
        # Duration efficiency
        task_duration = task.get('estimated_duration', task.get('duration', 30))
        utilization = task_duration / pool.available_minutes
        if 0.7 <= utilization <= 1.0:
            score += 0.15  # Good utilization
        elif utilization > 1.0:
            score -= 0.3  # Over-allocation penalty
        
        return min(1.0, max(0.0, score))
    
    def _resolve_conflicts(self, conflicts: List[Dict[str, Any]], strategy: ConflictResolutionStrategy) -> int:
        """Resolve scheduling conflicts using the specified strategy"""
        resolved_count = 0
        
        if strategy == ConflictResolutionStrategy.PRIORITY_FIRST:
            # Try to reschedule lower priority tasks to accommodate higher priority ones
            conflicts_by_priority = sorted(conflicts, key=lambda c: c.get('priority_score', 0), reverse=True)
            
            for conflict in conflicts_by_priority:
                # Implementation would involve complex rescheduling logic
                # For now, just log the conflict
                self.logger.info(f"Conflict resolution needed for task {conflict['task_id']}")
        
        return resolved_count
    
    def _calculate_optimization_score(self, assignments: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> float:
        """Calculate overall optimization score for the schedule"""
        if not assignments:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for assignment in assignments:
            assignment_score = assignment.get('assignment_score', 0.5)
            priority_weight = assignment.get('priority_score', 100) / 1000.0
            
            total_score += assignment_score * (1 + priority_weight)
            total_weight += (1 + priority_weight)
        
        optimization_score = total_score / total_weight if total_weight > 0 else 0.0
        return min(1.0, max(0.0, optimization_score))
    
    def _generate_recommendations(
        self, 
        assignments: List[Dict[str, Any]], 
        unscheduled: List[Dict[str, Any]], 
        conflicts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on scheduling results"""
        recommendations = []
        
        if unscheduled:
            recommendations.append(f"{len(unscheduled)} tasks could not be scheduled - consider extending time range or reducing task scope")
        
        if conflicts:
            recommendations.append(f"{len(conflicts)} scheduling conflicts detected - review task priorities and constraints")
        
        if assignments:
            avg_utilization = sum(a['allocated_minutes'] for a in assignments) / len(assignments)
            if avg_utilization < 30:
                recommendations.append("Low average task duration - consider batching small tasks for better efficiency")
            elif avg_utilization > 120:
                recommendations.append("High average task duration - consider breaking large tasks into smaller chunks")
        
        # Check for constraint violations
        soft_violations = sum(len(a.get('violated_soft_constraints', [])) for a in assignments)
        if soft_violations > 0:
            recommendations.append(f"{soft_violations} soft constraint violations - schedule may be suboptimal")
        
        return recommendations
    
    def _get_constraint_check_count(self) -> int:
        """Get number of constraint checks performed (would be tracked in real implementation)"""
        return len(self.constraint_engine.constraints) * 10  # Placeholder
    
    def _get_ai_analysis_count(self) -> int:
        """Get number of AI analyses performed (would be tracked in real implementation)"""
        return 5  # Placeholder
    
    def add_scheduling_constraint(self, constraint: SchedulingConstraint) -> bool:
        """Add a new scheduling constraint"""
        try:
            self.constraint_engine.add_constraint(constraint)
            return True
        except Exception as e:
            self.logger.error(f"Failed to add constraint: {e}")
            return False
    
    def remove_scheduling_constraint(self, constraint_id: str) -> bool:
        """Remove a scheduling constraint"""
        return self.constraint_engine.remove_constraint(constraint_id)
    
    def get_constraint_summary(self) -> Dict[str, Any]:
        """Get summary of active constraints"""
        return self.constraint_engine.get_constraints_summary()

# Global service instance
_smart_scheduling_service: Optional[SmartSchedulingService] = None

def get_smart_scheduling_service() -> SmartSchedulingService:
    """Get the global smart scheduling service instance"""
    global _smart_scheduling_service
    if not _smart_scheduling_service:
        _smart_scheduling_service = SmartSchedulingService()
    return _smart_scheduling_service