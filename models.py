from app_extensions import db

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String, nullable=False)
    user_id = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    model = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'  # Ensure this matches the table name in the schema
    session_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    database_name = db.Column(db.String, unique=True, nullable=False)
