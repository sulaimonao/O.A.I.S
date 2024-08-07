import logging
logging.basicConfig(level=logging.DEBUG)

from flask import Flask, session
from config import Config
from app_extensions import db, migrate, socketio
import os
import uuid

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_extensions(app)
    register_blueprints(app)
    
    @app.before_request
    def ensure_session_id():
        if 'id' not in session:
            session['id'] = str(uuid.uuid4())

    return app

def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")  # Ensure CORS is allowed

def register_blueprints(app):
    from routes import main
    app.register_blueprint(main)

if __name__ == "__main__":
    app = create_app()
    
    # Ensure necessary directories exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('virtual_workspace'):
        os.makedirs('virtual_workspace')
    
    socketio.run(app, debug=True)
