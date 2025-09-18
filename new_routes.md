# Add these routes to your routes/api.py file

# Import at the top of the file
from assignment_service import get_assignment_service

# Add these new endpoints for advanced assignment features

@api_bp.route('/api/assignments/smart-assign/<task_id>', methods=['POST'])
def smart_assign_task(task_id):
    """
    Intelligently assign a task using chunking strategies
    """
    assignment_service = get_assignment_service()
    
    data = request.json or {}
    max_pools = data.get('max_pools', 5)
    
    success, message, assignments = assignment_service.smart_assign_task(task_id, max_pools)
    
    if success:
        return jsonify({
            'status': 'success',
            'message': message,
            'assignments': assignments,
            'total_assigned': sum(a['allocated_minutes'] for a in assignments)
        })
    else:
        return jsonify({
            'status': 'error',
            'message': message
        }), 400

@api_bp.route('/api/assignments/bulk-assign-advanced', methods=['POST'])
def bulk_assign_advanced():
    """
    Advanced bulk assignment with category balancing and chunking
    """
    assignment_service = get_assignment_service()
    
    data = request.json or {}
    clear_existing = data.get('clear_existing', True)
    max_days_ahead = data.get('max_days_ahead', 7)
    
    result = assignment_service.bulk_assign_with_categories(
        clear_existing=clear_existing,
        max_days_ahead=max_days_ahead
    )
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@api_bp.route('/api/tasks/priority-scores', methods=['GET'])
def get_task_priority_scores():
    """
    Get all tasks with their advanced priority scores
    """
    assignment_service = get_assignment_service()
    
    tasks = Task.query.filter(Task.is_completed == False).all()
    task_scores = []
    
    for task in tasks:
        task_data = task.to_dict()
        task_data['is_overdue'] = task.due_date and task.due_date < date.today() if task.due_date else False
        
        score = assignment_service.calculate_advanced_priority_score(task_data)
        
        task_scores.append({
            'id': task.id,
            'title': task.title,
            'duration': task.duration,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'urgency': task.urgency,
            'priority': task.priority,
            'is_overdue': task_data['is_overdue'],
            'priority_score': score,
            'partial_completion': task.partial_completion_minutes or 0,
            'should_chunk': assignment_service.should_chunk_task(task_data)[0]
        })
    
    # Sort by priority score
    task_scores.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return jsonify({
        'tasks': task_scores,
        'total': len(task_scores)
    })

@api_bp.route('/api/tasks/<task_id>/chunking-strategy', methods=['GET'])
def get_task_chunking_strategy(task_id):
    """
    Get the recommended chunking strategy for a task
    """
    assignment_service = get_assignment_service()
    
    task = Task.query.get_or_404(task_id)
    task_data = task.to_dict()
    task_data['is_overdue'] = task.due_date and task.due_date < date.today() if task.due_date else False
    
    should_chunk, strategy = assignment_service.should_chunk_task(task_data)
    
    if should_chunk:
        # Get available pools to calculate chunk sizes
        today = date.today()
        end_date = today + timedelta(days=14)
        available_pools = TimePool.query.filter(
            TimePool.pool_date >= today,
            TimePool.pool_date <= end_date,
            TimePool.available_minutes > 0
        ).order_by(TimePool.pool_date, TimePool.start_time).all()
        
        chunk_sizes = assignment_service.calculate_chunk_sizes(task_data, strategy, available_pools)
        
        return jsonify({
            'should_chunk': True,
            'strategy': strategy,
            'chunk_sizes': chunk_sizes,
            'total_chunks': len(chunk_sizes),
            'remaining_work': task.duration - (task.partial_completion_minutes or 0)
        })
    else:
        return jsonify({
            'should_chunk': False,
            'reason': 'Task is too small or not divisible',
            'duration': task.duration
        })

@api_bp.route('/api/assignments/category-analysis', methods=['GET'])
def get_category_analysis():
    """
    Get task category analysis for balanced assignment
    """
    assignment_service = get_assignment_service()
    
    categories = assignment_service._categorize_tasks()
    
    # Calculate total available time
    today = date.today()
    end_date = today + timedelta(days=7)
    available_pools = TimePool.query.filter(
        TimePool.pool_date >= today,
        TimePool.pool_date <= end_date,
        TimePool.total_minutes > 0
    ).all()
    
    total_available = sum(p.available_minutes for p in available_pools)
    allocations = assignment_service._calculate_category_allocations(categories, total_available)
    
    analysis = {}
    for category_name, task_list in categories.items():
        analysis[category_name] = {
            'task_count': len(task_list),
            'total_duration': sum(t.get('duration', 0) for t in task_list),
            'allocated_time': allocations.get(category_name, 0),
            'top_tasks': [
                {
                    'id': t['id'],
                    'title': t['title'],
                    'priority_score': t.get('priority_score', 0),
                    'duration': t.get('duration', 0)
                } for t in task_list[:3]  # Top 3 tasks
            ]
        }
    
    return jsonify({
        'categories': analysis,
        'total_available_time': total_available,
        'pool_count': len(available_pools)
    })

@api_bp.route('/api/time-pools/<pool_id>/optimize-assignments', methods=['POST'])
def optimize_pool_assignments(pool_id):
    """
    Optimize assignments for a specific time pool based on context and time of day
    """
    assignment_service = get_assignment_service()
    
    pool = TimePool.query.get_or_404(pool_id)
    
    # Get current assignments
    current_assignments = TaskAssignment.query.filter_by(
        time_pool_id=pool_id,
        status='assigned'
    ).all()
    
    # Clear current assignments
    for assignment in current_assignments:
        assignment.cancel_assignment("Reoptimizing pool")
    
    db.session.commit()
    
    # Get available tasks and score them for this specific pool
    tasks = Task.query.filter(
        Task.is_completed == False
    ).all()
    
    scored_tasks = []
    for task in tasks:
        task_data = task.to_dict()
        score = assignment_service._calculate_pool_match_score(task_data, pool)
        scored_tasks.append({
            'task': task,
            'task_data': task_data,
            'score': score
        })
    
    # Sort by score
    scored_tasks.sort(key=lambda x: x['score'], reverse=True)
    
    # Reassign tasks to pool
    new_assignments = []
    remaining_minutes = pool.total_minutes
    
    for item in scored_tasks:
        if remaining_minutes <= 0:
            break
        
        task = item['task']
        allocation = min(task.duration or 30, remaining_minutes)
        
        success, message, assignment = assignment_service.assign_task_to_pool(
            task_id=task.id,
            time_pool_id=pool_id,
            allocated_minutes=allocation,
            assigned_by='optimization',
            notes=f"Optimized assignment (score: {item['score']:.1f})"
        )
        
        if success:
            new_assignments.append(assignment)
            remaining_minutes -= allocation
    
    return jsonify({
        'status': 'success',
        'original_assignments': len(current_assignments),
        'new_assignments': len(new_assignments),
        'assignments': new_assignments
    })

# Update the existing bulk assign endpoint to use the new logic
@api_bp.route('/api/assignments/bulk-assign', methods=['POST'])
def bulk_assign_tasks():
    """
    Perform bulk assignment of tasks to time pools with advanced logic
    """
    assignment_service = get_assignment_service()
    
    data = request.json or {}
    use_advanced = data.get('use_advanced', True)
    clear_existing = data.get('clear_existing', True)
    max_days_ahead = data.get('max_days_ahead', 7)
    
    if use_advanced:
        # Use the new category-balanced assignment
        result = assignment_service.bulk_assign_with_categories(
            clear_existing=clear_existing,
            max_days_ahead=max_days_ahead
        )
    else:
        # Use the original pool-by-pool method
        result = assignment_service.bulk_assign_tasks_to_pools(
            clear_existing=clear_existing,
            max_days_ahead=max_days_ahead
        )
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400