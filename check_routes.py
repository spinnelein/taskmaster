#!/usr/bin/env python3
"""
Check available routes in FastAPI app
NO EMOJIS
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from src.api.app import app

print('Available routes:')
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = [m for m in route.methods if m != 'HEAD']
        print(f'{route.path} - {methods}')