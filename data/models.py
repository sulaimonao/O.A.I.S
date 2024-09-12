from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    profile_data = db.Column(db.JSON)

    def __repr__(self):
        return f'<User {self.username}>'

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(120), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    model_used = db.Column(db.String(50), nullable=False)

class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    task_outcome = db.Column(db.String(50))  # success or failure
    feedback = db.Column(db.String(50))  # User feedback: satisfied, not satisfied
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
