# TaskMaster Upgrade Plan v3 - Flask Scheduling App
## Enhanced Assignment Service with Project/Event Awareness + Claude Integration

This plan is specifically designed for the Flask scheduling app that manages projects, tasks, events, meals, and time-based task assignment.

---

## PHASE 0: UNDERSTANDING THE SYSTEM

### Current Architecture:
```
TaskMaster Flask App
├── Projects → Phases → Tasks (with dependencies)
├── Events (calendar events, some linked to meals)
├── Meals → Dishes (meal planning system)
├── Time Pools (available work blocks)
├── Task Assignments (tasks → time pools)
└── Weather Integration (affects outdoor tasks)
```

### Key Relationships:
- Tasks belong to Projects/Phases with dependencies
- Events block time and can have meals attached
- Time Pools are work blocks between events
- Recurring tasks auto-regenerate (`recurrence_days`)
- Weather affects pool suitability

---

## PHASE 1: CORE ENHANCEMENTS FOR SCHEDULING APP

### Step 1.1: Project-Aware Priority Scoring
**File: `services/project_aware_priority_service.py`**

```python
class ProjectAwarePriorityService:
    """Priority scoring that understands project context and dependencies"""
    
    def calculate_priority_score(self, task: Dict, all_tasks: List[Dict] = None) -> float:
        """
        Enhanced scoring (0-1000 points):
        - Time criticality: 0-300 points
        - Project urgency: 0-200 points (phase deadlines, project priority)
        - Dependency impact: 0-200 points (blocking other tasks)
        - Progress momentum: 0-150 points (continue active projects)
        - Recurring task timing: 0-100 points
        - Quick wins: 0-50 points
        """
        score = 0.0
        
        # Base time criticality
        if task.get('due_date'):
            days_until_due = self._calculate_days_until_due(task['due_date'])
            if days_until_due < 0:  # Overdue
                score += 300 + (abs(days_until_due) * 10)
            elif days_until_due == 0:
                score += 250
            elif days_until_due <= 3:
                score += 150
            elif days_until_due <= 7:
                score += 100
        
        # Project/Phase context
        if task.get('project_id'):
            project = Project.query.get(task['project_id'])
            if project:
                # Project priority bonus
                priority_scores = {'HIGH': 150, 'MEDIUM': 100, 'LOW': 50}
                score += priority_scores.get(project.priority, 75)
                
                # Active project momentum
                if project.status == 'ACTIVE':
                    score += 50
                
                # Check phase deadlines
                if task.get('phase_id'):
                    phase = ProjectPhase.query.get(task['phase_id'])
                    if phase and phase.estimated_end_date:
                        phase_days = (phase.estimated_end_date.date() - date.today()).days
                        if phase_days <= 7:
                            score += 100  # Phase deadline approaching
        
        # Dependency impact - tasks that block others
        if all_tasks:
            blocked_count = sum(1 for t in all_tasks 
                              if task['id'] in (t.get('depends_on_task_ids', []) or []))
            score += min(blocked_count * 50, 200)  # Cap at 200
        
        # Recurring task timing
        if task.get('recurrence_days'):
            # Check how close to next recurrence
            if task.get('last_completed_at'):
                last_completed = datetime.fromisoformat(task['last_completed_at'])
                days_since = (datetime.now() - last_completed).days
                if days_since >= task['recurrence_days']:
                    score += 100  # Due for recurrence
                elif days_since >= task['recurrence_days'] * 0.8:
                    score += 50   # Coming up soon
        
        # Meal prep tasks get boost before meal time
        if task.get('meal_id'):
            meal = Meal.query.get(task['meal_id'])
            if meal and meal.serve_time:
                hours_until_meal = (meal.serve_time - datetime.now()).total_seconds() / 3600
                if hours_until_meal <= 24:
                    score += 150  # Meal is tomorrow or sooner
        
        return min(score, 1000)
    
    def get_task_context(self, task: Dict) -> Dict:
        """Get full context for a task including project/phase info"""
        context = {
            'task': task,
            'project': None,
            'phase': None,
            'dependencies': [],
            'blocks': [],
            'meal': None
        }
        
        if task.get('project_id'):
            context['project'] = Project.query.get(task['project_id']).to_dict()
        
        if task.get('phase_id'):
            context['phase'] = ProjectPhase.query.get(task['phase_id']).to_dict()
        
        if task.get('meal_id'):
            context['meal'] = Meal.query.get(task['meal_id']).to_dict()
        
        return context
```

### Step 1.2: Event-Aware Assignment Service
**File: `services/event_aware_assignment_service.py`**

```python
class EventAwareAssignmentService(FlaskAssignmentService):
    """Assignment service that respects events and project structure"""
    
    def __init__(self):
        super().__init__()
        self.priority_service = ProjectAwarePriorityService()
        self.chunking_service = TaskChunkingService()
    
    def get_available_pools_with_events(self, start_date: date, end_date: date) -> List[TimePool]:
        """Get time pools that don't conflict with events"""
        pools = TimePool.query.filter(
            TimePool.pool_date >= start_date,
            TimePool.pool_date <= end_date
        ).all()
        
        # Check each pool for event conflicts
        available_pools = []
        for pool in pools:
            if not self._has_event_conflict(pool):
                available_pools.append(pool)
        
        return available_pools
    
    def _has_event_conflict(self, pool: TimePool) -> bool:
        """Check if pool overlaps with any blocking events"""
        pool_start = datetime.combine(pool.pool_date, pool.start_time.time())
        pool_end = datetime.combine(pool.pool_date, pool.end_time.time())
        
        # Find overlapping events
        events = Event.query.filter(
            Event.is_blocking == True,
            Event.start_time < pool_end,
            Event.end_time > pool_start
        ).all()
        
        return len(events) > 0
    
    def assign_project_tasks_smart(self, project_id: str) -> Dict:
        """Assign all tasks in a project respecting dependencies"""
        project = Project.query.get(project_id)
        if not project:
            return {'success': False, 'message': 'Project not found'}
        
        # Get all project tasks
        tasks = Task.query.filter_by(
            project_id=project_id,
            is_completed=False
        ).all()
        
        # Build dependency graph
        task_graph = self._build_dependency_graph(tasks)
        
        # Get topological order (respecting dependencies)
        ordered_tasks = self._topological_sort(task_graph)
        
        # Assign in dependency order
        assignments = []
        for task in ordered_tasks:
            # Only assign if dependencies are complete/assigned
            if self._dependencies_satisfied(task):
                result = self._assign_task_smartly(task)
                if result:
                    assignments.append(result)
        
        return {
            'success': True,
            'project': project.title,
            'tasks_assigned': len(assignments),
            'assignments': assignments
        }
    
    def handle_recurring_tasks(self) -> Dict:
        """Process recurring tasks that need regeneration"""
        current_time = datetime.now()
        
        # Find recurring tasks that need processing
        recurring_tasks = Task.query.filter(
            Task.recurrence_days > 0,
            Task.is_snoozed == True,
            Task.snoozed_until <= current_time
        ).all()
        
        processed = []
        for task in recurring_tasks:
            # Unsnooze the task
            task.is_snoozed = False
            task.snoozed_until = None
            task.status = 'active'
            
            # Reset any partial completion
            task.partial_completion_minutes = 0
            
            processed.append(task.title)
        
        db.session.commit()
        
        return {
            'processed': len(processed),
            'tasks': processed
        }
    
    def prepare_meal_tasks(self, date_range: int = 3) -> Dict:
        """Create tasks for upcoming meal preparation"""
        end_date = datetime.now() + timedelta(days=date_range)
        
        # Find upcoming meals
        meals = Meal.query.filter(
            Meal.planned_date <= end_date,
            Meal.status == 'planned'
        ).all()
        
        tasks_created = []
        for meal in meals:
            # Create prep task if needed
            hours_before_meal = (meal.serve_time - datetime.now()).total_seconds() / 3600
            
            if hours_before_meal <= 48:  # Within 2 days
                # Check if task already exists
                existing = Task.query.filter_by(
                    meal_id=meal.id,
                    title=f"Prepare {meal.title}"
                ).first()
                
                if not existing:
                    # Calculate prep time
                    total_prep = 0
                    for dish in meal.get_dishes():
                        total_prep += (dish.prep_time_minutes or 30)
                    
                    task = Task(
                        id=str(uuid.uuid4()),
                        title=f"Prepare {meal.title}",
                        description=f"Prep for {meal.meal_type}: {meal.title}",
                        duration=total_prep,
                        urgency=8,  # High urgency for meal prep
                        due_date=meal.planned_date.date() if meal.planned_date else None,
                        meal_id=meal.id,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    db.session.add(task)
                    tasks_created.append(task.title)
        
        db.session.commit()
        
        return {
            'meals_checked': len(meals),
            'tasks_created': len(tasks_created),
            'tasks': tasks_created
        }
```

### Step 1.3: Claude Service with Project Context
**File: `services/claude_task_analyzer.py`**

```python
class ClaudeTaskAnalyzer:
    """Claude integration that understands the app's context"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
    
    def analyze_task_in_context(self, task_title: str, project_context: Dict = None) -> Dict:
        """Analyze task with project/phase context"""
        
        # Build context prompt
        context_info = ""
        if project_context:
            if project_context.get('project'):
                context_info += f"Project: {project_context['project']['title']}\n"
                context_info += f"Priority: {project_context['project']['priority']}\n"
            if project_context.get('phase'):
                context_info += f"Phase: {project_context['phase']['title']}\n"
            if project_context.get('meal'):
                context_info += f"Meal: {project_context['meal']['title']}\n"
                context_info += f"Meal Type: {project_context['meal']['meal_type']}\n"
        
        if self.client:
            return self._call_claude_with_context(task_title, context_info)
        else:
            return self._smart_keyword_analysis(task_title, project_context)
    
    def suggest_task_breakdown(self, task_title: str, duration: int) -> List[Dict]:
        """Get Claude to suggest how to break down a large task"""
        
        if not self.client:
            # Simple fallback
            if duration <= 90:
                return [{'title': task_title, 'duration': duration}]
            
            chunks = duration // 60
            return [
                {'title': f"{task_title} - Part {i+1}", 'duration': 60}
                for i in range(chunks)
            ]
        
        prompt = f"""Break down this task into logical subtasks: "{task_title}"
        Total duration: {duration} minutes
        
        Return a JSON array of subtasks, each with:
        - title: descriptive subtask name
        - duration: minutes (15-90 per subtask)
        - order: sequence number
        
        Make the subtasks logical and actionable."""
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            return json.loads(response.content[0].text)
        except:
            return [{'title': task_title, 'duration': duration, 'order': 1}]
    
    def _smart_keyword_analysis(self, title: str, context: Dict = None) -> Dict:
        """Enhanced keyword analysis using context"""
        title_lower = title.lower()
        
        # Base duration from keywords
        duration = 60  # default
        
        # Adjust based on project context
        if context and context.get('project'):
            project_priority = context['project'].get('priority', 'MEDIUM')
            if project_priority == 'HIGH':
                # High priority projects might need more thorough work
                duration = int(duration * 1.2)
        
        # Check for meal-related tasks
        if context and context.get('meal'):
            # Meal prep tasks have specific timing
            if 'shop' in title_lower or 'buy' in title_lower:
                duration = 45  # Shopping
            elif 'prep' in title_lower or 'prepare' in title_lower:
                duration = 60  # Prep work
            elif 'cook' in title_lower:
                duration = 90  # Cooking
        
        # Check for project phase keywords
        if 'design' in title_lower or 'plan' in title_lower:
            duration = 120
        elif 'implement' in title_lower or 'build' in title_lower:
            duration = 180
        elif 'test' in title_lower or 'review' in title_lower:
            duration = 90
        elif 'deploy' in title_lower or 'launch' in title_lower:
            duration = 120
        
        # Outdoor task detection
        outdoor_keywords = ['mow', 'garden', 'yard', 'lawn', 'trim', 'plant', 
                          'outdoor', 'wash car', 'gutter', 'paint exterior']
        is_outdoor = any(keyword in title_lower for keyword in outdoor_keywords)
        
        return {
            'estimated_duration_minutes': duration,
            'is_divisible': duration > 90,
            'min_chunk_minutes': 30 if duration > 90 else duration,
            'cognitive_load': 'high' if 'design' in title_lower or 'analyze' in title_lower else 'medium',
            'best_time_of_day': 'morning' if 'review' in title_lower else 'anytime',
            'requires_focused_time': 'write' in title_lower or 'design' in title_lower,
            'weather_sensitive': is_outdoor,
            'energy_level': 'high' if is_outdoor else 'medium',
            'suggested_context_tags': self._suggest_context_tags(title_lower)
        }
    
    def _suggest_context_tags(self, title_lower: str) -> List[str]:
        """Suggest context tags for time pools"""
        tags = []
        
        if any(word in title_lower for word in ['email', 'call', 'meeting']):
            tags.append('communication')
        if any(word in title_lower for word in ['write', 'document', 'report']):
            tags.append('deep_work')
        if any(word in title_lower for word in ['code', 'program', 'debug']):
            tags.append('coding')
        if any(word in title_lower for word in ['review', 'analyze', 'evaluate']):
            tags.append('analysis')
        
        return tags
```

### Step 1.4: Unified Smart Scheduling Service
**File: `services/smart_scheduling_service.py`**

```python
class SmartSchedulingService:
    """Unified service that coordinates all scheduling components"""
    
    def __init__(self):
        self.assignment_service = EventAwareAssignmentService()
        self.claude_analyzer = ClaudeTaskAnalyzer()
        self.weather_service = get_flask_weather_service()
    
    def daily_scheduling_routine(self) -> Dict:
        """Daily routine to prepare and assign tasks"""
        results = {}
        
        # Step 1: Handle recurring tasks
        recurring_result = self.assignment_service.handle_recurring_tasks()
        results['recurring_tasks'] = recurring_result
        
        # Step 2: Create meal prep tasks
        meal_result = self.assignment_service.prepare_meal_tasks()
        results['meal_tasks'] = meal_result
        
        # Step 3: Update weather forecasts
        weather_updated = self.weather_service.update_forecast_from_api()
        results['weather_updated'] = weather_updated
        
        # Step 4: Smart bulk assignment
        assignment_result = self.smart_assign_all_tasks(incremental=True)
        results['assignments'] = assignment_result
        
        return results
    
    def smart_assign_all_tasks(self, incremental: bool = True) -> Dict:
        """Main assignment logic with all enhancements"""
        
        # Get all tasks with full context
        tasks = self._get_enriched_task_queue()
        
        # Get available pools (checking events)
        today = date.today()
        end_date = today + timedelta(days=7)
        pools = self.assignment_service.get_available_pools_with_events(today, end_date)
        
        # Group tasks by project for better flow
        tasks_by_project = self._group_tasks_by_project(tasks)
        
        assignments_made = []
        
        # Assign project tasks first (maintaining flow)
        for project_id, project_tasks in tasks_by_project.items():
            if project_id:  # Has a project
                for task in project_tasks:
                    if self._can_assign_task(task):
                        assignment = self._assign_with_chunking(task, pools)
                        if assignment:
                            assignments_made.extend(assignment)
        
        # Then assign standalone tasks
        standalone_tasks = tasks_by_project.get(None, [])
        for task in standalone_tasks:
            assignment = self._assign_with_chunking(task, pools)
            if assignment:
                assignments_made.extend(assignment)
        
        return {
            'success': True,
            'total_tasks': len(tasks),
            'assignments_made': len(assignments_made),
            'pools_used': len(set(a['pool_id'] for a in assignments_made)),
            'assignments': assignments_made
        }
    
    def _get_enriched_task_queue(self) -> List[Dict]:
        """Get tasks with full context and priority scores"""
        tasks = Task.query.filter(Task.is_completed == False).all()
        
        enriched_tasks = []
        all_task_dicts = [t.to_dict() for t in tasks]
        
        for task in tasks:
            task_dict = task.to_dict()
            
            # Add project context
            context = self.assignment_service.priority_service.get_task_context(task_dict)
            
            # Calculate priority with context
            task_dict['priority_score'] = self.assignment_service.priority_service.calculate_priority_score(
                task_dict, 
                all_task_dicts
            )
            
            # Add context
            task_dict['context'] = context
            
            enriched_tasks.append(task_dict)
        
        # Sort by priority
        enriched_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return enriched_tasks
    
    def _assign_with_chunking(self, task: Dict, pools: List[TimePool]) -> List[Dict]:
        """Assign task with intelligent chunking if needed"""
        assignments = []
        
        # Check if task should be chunked
        if task.get('is_divisible') and task.get('duration', 0) > 120:
            # Get Claude's suggestion for breakdown
            subtasks = self.claude_analyzer.suggest_task_breakdown(
                task['title'], 
                task['duration']
            )
            
            for subtask in subtasks:
                # Find best pool for this chunk
                for pool in pools:
                    if pool.available_minutes >= subtask['duration']:
                        success, msg, assignment = self.assignment_service.assign_task_to_pool(
                            task['id'],
                            pool.id,
                            subtask['duration'],
                            notes=subtask['title']
                        )
                        if success:
                            assignments.append(assignment)
                            break
        else:
            # Assign whole task
            for pool in pools:
                if pool.available_minutes >= task.get('duration', 60):
                    # Check weather compatibility
                    if task.get('required_weather') == 'outdoor':
                        weather = pool.get_weather_forecast()
                        if weather and not weather.is_suitable_for_outdoor_work():
                            continue
                    
                    success, msg, assignment = self.assignment_service.assign_task_to_pool(
                        task['id'],
                        pool.id,
                        task['duration']
                    )
                    if success:
                        assignments.append(assignment)
                        break
        
        return assignments
```

---

## PHASE 2: API ENDPOINTS FOR SCHEDULING APP

### Step 2.1: Smart Scheduling Endpoints
**File: `routes/smart_scheduling_routes.py`**

```python
from flask import Blueprint, request, jsonify
from services.smart_scheduling_service import SmartSchedulingService

smart_bp = Blueprint('smart', __name__)
service = SmartSchedulingService()

@smart_bp.route('/api/schedule/daily-routine', methods=['POST'])
def run_daily_routine():
    """Run the complete daily scheduling routine"""
    results = service.daily_scheduling_routine()
    
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'results': results
    })

@smart_bp.route('/api/projects/<project_id>/smart-assign', methods=['POST'])
def smart_assign_project(project_id):
    """Smart assignment for all tasks in a project"""
    result = service.assignment_service.assign_project_tasks_smart(project_id)
    return jsonify(result)

@smart_bp.route('/api/tasks/analyze-with-context', methods=['POST'])
def analyze_task_with_context():
    """Analyze task with project/meal context"""
    data = request.json
    title = data.get('title')
    project_id = data.get('project_id')
    phase_id = data.get('phase_id')
    meal_id = data.get('meal_id')
    
    # Build context
    context = {}
    if project_id:
        context['project'] = Project.query.get(project_id).to_dict()
    if phase_id:
        context['phase'] = ProjectPhase.query.get(phase_id).to_dict()
    if meal_id:
        context['meal'] = Meal.query.get(meal_id).to_dict()
    
    analysis = service.claude_analyzer.analyze_task_in_context(title, context)
    
    return jsonify({
        'title': title,
        'context': context,
        'analysis': analysis
    })

@smart_bp.route('/api/tasks/<task_id>/suggest-breakdown', methods=['GET'])
def suggest_task_breakdown(task_id):
    """Get Claude's suggestion for breaking down a large task"""
    task = Task.query.get_or_404(task_id)
    
    if not task.is_divisible or task.duration <= 90:
        return jsonify({
            'task_id': task_id,
            'suggestions': [{'title': task.title, 'duration': task.duration}]
        })
    
    suggestions = service.claude_analyzer.suggest_task_breakdown(
        task.title, 
        task.duration
    )
    
    return jsonify({
        'task_id': task_id,
        'total_duration': task.duration,
        'suggestions': suggestions
    })

@smart_bp.route('/api/schedule/optimize-week', methods=['POST'])
def optimize_week():
    """Optimize the entire week's schedule"""
    data = request.json
    
    # Run smart assignment for the week
    result = service.smart_assign_all_tasks(
        incremental=data.get('incremental', True)
    )
    
    # Get weekly summary
    today = date.today()
    week_end = today + timedelta(days=7)
    
    assignments_by_day = {}
    for assignment in result.get('assignments', []):
        pool = TimePool.query.get(assignment['pool_id'])
        day = pool.pool_date.isoformat()
        if day not in assignments_by_day:
            assignments_by_day[day] = []
        assignments_by_day[day].append(assignment)
    
    return jsonify({
        'success': True,
        'week_start': today.isoformat(),
        'week_end': week_end.isoformat(),
        'total_assignments': result['assignments_made'],
        'assignments_by_day': assignments_by_day,
        'summary': result
    })

@smart_bp.route('/api/meals/prepare-tasks', methods=['POST'])
def prepare_meal_tasks():
    """Create tasks for upcoming meal preparation"""
    days_ahead = request.json.get('days_ahead', 3)
    result = service.assignment_service.prepare_meal_tasks(days_ahead)
    return jsonify(result)
```

---

## PHASE 3: TESTING FOR SCHEDULING APP

### Step 3.1: Integration Tests
**File: `tests/test_smart_scheduling.py`**

```python
import pytest
from app import app, db
from models import Task, Project, ProjectPhase, Event, Meal, TimePool
from services.smart_scheduling_service import SmartSchedulingService

class TestSmartScheduling:
    
    @pytest.fixture
    def setup_test_data(self):
        """Create realistic test data"""
        with app.app_context():
            # Create a project with phases
            project = Project(
                id='test-project-1',
                title='Website Redesign',
                status='ACTIVE',
                priority='HIGH'
            )
            db.session.add(project)
            
            phase1 = ProjectPhase(
                id='phase-1',
                title='Design Phase',
                project_id=project.id,
                order=1
            )
            db.session.add(phase1)
            
            # Create tasks with dependencies
            task1 = Task(
                id='task-1',
                title='Create wireframes',
                duration=120,
                project_id=project.id,
                phase_id=phase1.id,
                urgency=8
            )
            
            task2 = Task(
                id='task-2',
                title='Review wireframes',
                duration=60,
                project_id=project.id,
                phase_id=phase1.id,
                depends_on_task_ids='["task-1"]',
                urgency=7
            )
            
            db.session.add_all([task1, task2])
            
            # Create a blocking event
            event = Event(
                id='event-1',
                title='Team Meeting',
                start_time=datetime.combine(date.today(), time(10, 0)),
                end_time=datetime.combine(date.today(), time(11, 0)),
                is_blocking=True
            )
            db.session.add(event)
            
            # Create time pools
            for i in range(3):
                pool = TimePool(
                    id=f'pool-{i}',
                    pool_date=date.today() + timedelta(days=i),
                    start_time=datetime.combine(date.today(), time(9, 0)),
                    end_time=datetime.combine(date.today(), time(17, 0)),
                    total_minutes=480,
                    available_minutes=480
                )
                db.session.add(pool)
            
            db.session.commit()
    
    def test_project_aware_assignment(self, setup_test_data):
        """Test that project tasks are assigned respecting dependencies"""
        service = SmartSchedulingService()
        
        result = service.assignment_service.assign_project_tasks_smart('test-project-1')
        
        assert result['success'] == True
        assert result['tasks_assigned'] >= 1
        
        # Verify task1 is assigned before task2 (dependency)
        assignments = result['assignments']
        task1_pool = next((a for a in assignments if a['task_id'] == 'task-1'), None)
        task2_pool = next((a for a in assignments if a['task_id'] == 'task-2'), None)
        
        if task1_pool and task2_pool:
            pool1 = TimePool.query.get(task1_pool['pool_id'])
            pool2 = TimePool.query.get(task2_pool['pool_id'])
            assert pool1.pool_date <= pool2.pool_date
    
    def test_event_conflict_detection(self, setup_test_data):
        """Test that assignments avoid event conflicts"""
        service = SmartSchedulingService()
        
        # Get pools with event checking
        pools = service.assignment_service.get_available_pools_with_events(
            date.today(),
            date.today() + timedelta(days=1)
        )
        
        # Verify pool during event time is excluded or adjusted
        for pool in pools:
            pool_start = datetime.combine(pool.pool_date, pool.start_time.time())
            pool_end = datetime.combine(pool.pool_date, pool.end_time.time())
            
            # Should not overlap with team meeting (10-11am today)
            if pool.pool_date == date.today():
                meeting_start = datetime.combine(date.today(), time(10, 0))
                meeting_end = datetime.combine(date.today(), time(11, 0))
                
                # Pool should not overlap with meeting
                assert not (pool_start < meeting_end and pool_end > meeting_start)
    
    def test_meal_task_generation(self):
        """Test automatic meal prep task creation"""
        with app.app_context():
            # Create a meal for tomorrow
            meal = Meal(
                id='meal-1',
                title='Thanksgiving Dinner',
                meal_type='dinner',
                planned_date=datetime.now() + timedelta(days=1),
                serve_time=datetime.now() + timedelta(days=1, hours=18),
                status='planned'
            )
            db.session.add(meal)
            db.session.commit()
            
            service = SmartSchedulingService()
            result = service.assignment_service.prepare_meal_tasks(days=3)
            
            assert result['tasks_created'] >= 1
            assert 'Prepare Thanksgiving Dinner' in result['tasks']
    
    def test_recurring_task_handling(self):
        """Test recurring task processing"""
        with app.app_context():
            # Create a recurring task that's due
            task = Task(
                id='recurring-1',
                title='Weekly Report',
                duration=60,
                recurrence_days=7,
                is_snoozed=True,
                snoozed_until=datetime.now() - timedelta(hours=1),  # Past due
                last_completed_at=datetime.now() - timedelta(days=8)
            )
            db.session.add(task)
            db.session.commit()
            
            service = SmartSchedulingService()
            result = service.assignment_service.handle_recurring_tasks()
            
            assert result['processed'] == 1
            assert 'Weekly Report' in result['tasks']
            
            # Verify task is unsnoozed
            updated_task = Task.query.get('recurring-1')
            assert updated_task.is_snoozed == False
    
    def test_daily_routine(self, setup_test_data):
        """Test complete daily scheduling routine"""
        service = SmartSchedulingService()
        
        results = service.daily_scheduling_routine()
        
        assert 'recurring_tasks' in results
        assert 'meal_tasks' in results
        assert 'assignments' in results
        assert results['assignments']['success'] == True
```

---

## MIGRATION & DEPLOYMENT

### Database Migration:
```sql
-- Add new columns to tasks table
ALTER TABLE tasks ADD COLUMN cognitive_load VARCHAR(20);
ALTER TABLE tasks ADD COLUMN ai_analysis TEXT;
ALTER TABLE tasks ADD COLUMN last_analyzed TIMESTAMP;
ALTER TABLE tasks ADD COLUMN energy_level VARCHAR(20);

-- Add context tags to time_pools if not exists
ALTER TABLE time_pools_flask ADD COLUMN IF NOT EXISTS context_tags TEXT;
```

### Environment Variables:
```bash
# .env
ANTHROPIC_API_KEY=your-api-key-here
OPENWEATHER_API_KEY=your-weather-api-key
WEATHER_LOCATION=Seattle,WA,US
```

### Deployment Steps:
1. Run database migrations
2. Deploy new service files
3. Test with existing data
4. Enable daily routine cron job
5. Monitor performance

---

## KEY IMPROVEMENTS FOR FLASK SCHEDULING APP

1. **Project-Aware Prioritization**: Understands project deadlines, phases, and dependencies
2. **Event Conflict Detection**: Won't schedule during meetings/events
3. **Meal Task Integration**: Automatically creates prep tasks for upcoming meals
4. **Recurring Task Support**: Handles the existing recurrence_days field properly
5. **Dependency Respect**: Assigns tasks in correct order within projects
6. **Weather-Aware**: Uses existing weather system for outdoor tasks
7. **Time Pool Context**: Uses context_tags field for better matching
8. **Daily Routine**: Single endpoint to handle all daily scheduling needs

---

## SUCCESS METRICS

### Scheduling Quality:
- No task assigned during blocking events
- Project tasks maintain dependency order
- Meal prep tasks created 24-48 hours before meals
- Recurring tasks processed on schedule

### Performance:
- Daily routine completes in < 5 seconds
- Project assignment respects all dependencies
- Claude analysis cached to reduce API calls

### User Experience:
- Single button to optimize daily/weekly schedule
- Clear visibility into project progress
- Automatic meal task generation
- Respect for work/personal time boundaries

This revised plan is specifically tailored to the Flask scheduling app's actual purpose and structure, making it much more practical and valuable for the existing system.