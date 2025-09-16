from flask import Flask, render_template
import os

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Use existing database (in backend directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    database_path = os.path.join(project_root, 'backend', 'taskmaster.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SECRET_KEY'] = 'dev'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    from models import db
    db.init_app(app)
    
    # Register blueprints
    from routes.api import api_bp
    app.register_blueprint(api_bp)
    
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
    
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'TaskMaster Flask'}
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)