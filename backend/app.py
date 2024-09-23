# backend/app.py

from flask import Flask, render_template, send_from_directory
from flask_session import Session
from flask_cors import CORS
from flask_socketio import SocketIO
from .config import Config
from .models.db import db, migrate
from .api.routes import api_bp
from .socketio.handlers import socketio_handlers
import os

socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    Session(app)
    CORS(app, resources={r"/*": {"origins": "*"}})  # Adjust CORS as needed

    # Register Blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    # Initialize SocketIO
    socketio.init_app(app)
    socketio_handlers(socketio)

    # Serve the React frontend from the public folder
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and os.path.exists(f'../frontend/public/{path}'):
            return send_from_directory('../frontend/public', path)
        else:
            return render_template('index.html')

    return app

app = create_app()
