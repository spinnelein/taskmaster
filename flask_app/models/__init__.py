# __init__.py - Models package initialization and exports
"""
Models package for TaskMaster Flask application.

This package contains domain-based model modules following single responsibility principle:
- base: Base model classes and shared functionality 
- core: Core entities (Event, Task, TimePool)
- projects: Project domain (Initiative, Project, ProjectPhase)
- meals: Meal domain (Meal, Dish, Recipe, MealDish)
- system: System models (WeatherForecast, TaskAssignment)

All models are exported from this package for convenient importing.
"""

# Import the database instance
from .base import db

# Import all models from domain modules
from .core import Event, Task, TimePool
from .projects import Initiative, Project, ProjectPhase, ProjectTemplate
from .meals import Dish, Meal, Recipe, MealDish
from .system import WeatherForecast, TaskAssignment
from .saved_searches import SavedSearch, SearchTemplate
from .webhooks import WebhookSubscription, WebhookDelivery, WebhookEvent, WebhookStatus, DeliveryStatus
from .analytics import APIUsageMetric, SearchAnalytic, APIKey, RateLimitRecord, MetricType

# Export all models and db for easy importing
__all__ = [
    'db',
    'Event',
    'Task', 
    'TimePool',
    'Initiative',
    'Project',
    'ProjectPhase',
    'ProjectTemplate',
    'Dish',
    'Meal',
    'Recipe',
    'MealDish',
    'WeatherForecast',
    'TaskAssignment',
    'SavedSearch',
    'SearchTemplate',
    'WebhookSubscription',
    'WebhookDelivery',
    'WebhookEvent',
    'WebhookStatus',
    'DeliveryStatus',
    'APIUsageMetric',
    'SearchAnalytic',
    'APIKey',
    'RateLimitRecord',
    'MetricType'
]