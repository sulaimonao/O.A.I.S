from flask import Flask
from config import Config
from app_extensions import db, migrate, socketio
from routes import main
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_extensions(app)
    register_blueprints(app)

    return app

def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

def register_blueprints(app):
    app.register_blueprint(main)

if __name__ == "__main__":
    app = create_app()
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('virtual_workspace'):
        os.makedirs('virtual_workspace')
    socketio.run(app, debug=True)
