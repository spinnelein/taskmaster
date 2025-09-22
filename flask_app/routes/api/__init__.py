"""
API Routes Package

This package contains modular API route blueprints organized by resource domain.
Each module handles a specific set of related endpoints following REST conventions.

Modules:
- core: Health checks, enhanced queue, event-aware assignments, legacy endpoints
- events: Event CRUD, recurring events, calendar integration
- tasks: Task CRUD, completion, dependencies, snoozing
- initiatives: Initiative management and task creation
- projects: Project CRUD, project templates, template instantiation
- assignments: Task-to-pool assignments and suggestions
- schedule: Task queue, time pools, scheduling operations
- meals: Meal planning, dish management, meal-event integration
- analysis: Claude AI analysis, complexity assessment, optimization

Enhanced v2 API Modules:
- tasks_enhanced: v2 tasks API with pagination, filtering, sorting, batch operations
- events_enhanced: v2 events API with advanced queries, calendar optimization

Advanced Features Modules:
- search: Comprehensive search with FTS, faceting, suggestions, query analysis
- export: Multi-format data export with streaming, filtering, and scheduled exports
- webhooks: Event-driven webhooks with HMAC security, retry logic, and analytics
- analytics: API usage tracking, performance monitoring, rate limiting, and insights
"""
from flask import Blueprint

# Import all sub-blueprints
from .core import core_bp
from .events import events_bp
from .tasks import tasks_bp
from .initiatives import initiatives_bp
from .projects import projects_bp
from .assignments import assignments_bp
from .schedule import schedule_bp
from .meals import meals_bp
from .analysis import analysis_bp
from .smart_scheduling import smart_scheduling_bp

# Import enhanced v2 blueprints
from .tasks_enhanced import tasks_enhanced_bp
from .events_enhanced import events_enhanced_bp

# Import performance optimization blueprint
from .performance import performance_bp

# Import advanced features blueprints
from .search import search_bp
from .export import export_bp
from .webhooks import webhook_bp
from .analytics import analytics_bp

# Create the main API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Register all sub-blueprints
api_bp.register_blueprint(core_bp)
api_bp.register_blueprint(events_bp)
api_bp.register_blueprint(tasks_bp)
api_bp.register_blueprint(initiatives_bp)
api_bp.register_blueprint(projects_bp)
api_bp.register_blueprint(assignments_bp)
api_bp.register_blueprint(schedule_bp)
api_bp.register_blueprint(meals_bp)
api_bp.register_blueprint(analysis_bp)
api_bp.register_blueprint(smart_scheduling_bp)

# Register enhanced v2 blueprints
api_bp.register_blueprint(tasks_enhanced_bp)
api_bp.register_blueprint(events_enhanced_bp)

# Register performance optimization blueprint
api_bp.register_blueprint(performance_bp)

# Register advanced features blueprints
api_bp.register_blueprint(search_bp)
api_bp.register_blueprint(export_bp)
api_bp.register_blueprint(webhook_bp)
api_bp.register_blueprint(analytics_bp)