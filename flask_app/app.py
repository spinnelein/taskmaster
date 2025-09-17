from flask import Flask, render_template
import os

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Use existing database (moved to root directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.path.join(project_root, 'taskmaster.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SECRET_KEY'] = 'dev'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    # Register blueprints
    from routes.api import api_bp
    from routes.projects import projects_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(projects_bp)
    
    # Main routes
    @app.route('/')
    def index():
        return render_template('schedule.html')
    
    @app.route('/events')
    @app.route('/events/')
    def events():
        return render_template('events.html')
    
    @app.route('/tasks')
    @app.route('/tasks/')
    def tasks():
        return render_template('tasks.html')
    
    @app.route('/initiatives')
    @app.route('/initiatives/')
    def initiatives():
        return render_template('initiatives.html')
    
    @app.route('/events/<event_id>/edit')
    def edit_event(event_id):
        from models import Event
        
        # Check if this is a recurring event instance ID (format: master_id_date)
        if '_' in event_id and len(event_id.split('_')) >= 2:
            # This is a recurring event instance, extract the master event ID
            parts = event_id.split('_')
            master_event_id = '_'.join(parts[:-1])  # Everything except the last part (date)
            instance_date = parts[-1]  # The date part
            
            # Try to find the master event
            event = Event.query.get(master_event_id)
            if not event:
                # If master not found, try the full ID as a fallback
                event = Event.query.get_or_404(event_id)
            
            # Pass the instance date for context
            return render_template('edit_event.html', event=event, instance_date=instance_date)
        else:
            # Regular event ID
            event = Event.query.get_or_404(event_id)
            return render_template('edit_event.html', event=event)
    
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'TaskMaster Flask'}
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Initialize and start background service
    from background_service import background_service
    background_service.init_app(app)
    
    # Start the background service automatically
    try:
        if not background_service.is_running:
            background_service.start()
            app.logger.info("Background service started successfully")
    except Exception as e:
        app.logger.error(f"Failed to start background service: {e}")
    
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    # For development - start background service immediately
    with app.app_context():
        from background_service import background_service
        if not background_service.is_running:
            background_service.start()
    
    app.run(debug=True, port=5000)