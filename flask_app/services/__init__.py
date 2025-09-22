"""
TaskMaster Services Package
Provides modular service architecture for the TaskMaster Flask application
"""

# Background services are available through the background subpackage
from . import background

__all__ = ["background"]
