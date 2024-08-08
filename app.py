import logging
import os
from flask import Flask, session
from config import Config
from app_extensions import db, migrate, socketio
import uuid
from utils.database import init_db, check_and_create_tables

# Set up logging based on the environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
if ENVIRONMENT == 'development':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
elif ENVIRONMENT == 'production':
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_extensions(app)
    register_blueprints(app)

    @app.before_request
    def ensure_session_id():
        if 'id' not in session:
            session['id'] = str(uuid.uuid4())

        if 'user_profile' in session:
            profile_db = session['user_profile']['database_name']
            app.config['SQLALCHEMY_BINDS'] = {
                'profile': f'sqlite:///{profile_db}'
            }
            db.engine.dispose()
            db.create_all(bind='profile')

    return app

def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")  # Ensure CORS is allowed

def register_blueprints(app):
    from routes import main
    app.register_blueprint(main)

if __name__ == "__main__":
    init_db()  # Initialize the main database
    check_and_create_tables()  # Ensure necessary tables exist
    app = create_app()
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('virtual_workspace'):
        os.makedirs('virtual_workspace')
    socketio.run(app, debug=True)
