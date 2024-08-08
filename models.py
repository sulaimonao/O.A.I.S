from app_extensions import db

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    session_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    database_name = db.Column(db.String, unique=True, nullable=False)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String, nullable=False)
    user_id = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    model = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)

class LongTermMemory(db.Model):
    __tablename__ = 'long_term_memory'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)

class ChatroomMemory(db.Model):
    __tablename__ = 'chatroom_memory'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
