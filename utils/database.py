from app_extensions import db
from models import UserProfile, Message, LongTermMemory, ChatroomMemory
import logging

logging.basicConfig(level=logging.INFO)

def init_db():
    logging.info("Initializing database...")
    try:
        db.create_all()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")

def query_db(model, filters=None, one=False):
    try:
        query = model.query
        if filters:
            query = query.filter_by(**filters)
        result = query.first() if one else query.all()
        return result
    except Exception as e:
        logging.error(f"Database query failed: {e}")
        return None

def add_message(session_id, user_id, role, content, model_name):
    try:
        message = Message(session_id=session_id, user_id=user_id, role=role, content=content, model=model_name)
        db.session.add(message)
        db.session.commit()
    except Exception as e:
        logging.error(f"Failed to add message: {e}")
        db.session.rollback()

def add_long_term_memory(session_id, content):
    try:
        memory = LongTermMemory(session_id=session_id, content=content)
        db.session.add(memory)
        db.session.commit()
    except Exception as e:
        logging.error(f"Failed to add long-term memory: {e}")
        db.session.rollback()

def add_chatroom_memory(session_id, content):
    try:
        memory = ChatroomMemory(session_id=session_id, content=content)
        db.session.add(memory)
        db.session.commit()
    except Exception as e:
        logging.error(f"Failed to add chatroom memory: {e}")
        db.session.rollback()

def get_conversation_history(session_id):
    try:
        return query_db(Message, filters={'session_id': session_id})
    except Exception as e:
        logging.error(f"Failed to get conversation history: {e}")
        return []

def get_user_profile(session_id):
    try:
        return query_db(UserProfile, filters={'session_id': session_id}, one=True)
    except Exception as e:
        logging.error(f"Failed to get user profile: {e}")
        return None

def set_user_profile(session_id, name):
    try:
        profile = UserProfile(session_id=session_id, name=name, database_name=f'{name}_database.db')
        db.session.add(profile)
        db.session.commit()
    except Exception as e:
        logging.error(f"Failed to set user profile: {e}")
        db.session.rollback()

def get_existing_profiles():
    try:
        profiles = UserProfile.query.all()
        return [profile.name for profile in profiles]
    except Exception as e:
        logging.error(f"Failed to get existing profiles: {e}")
        return []

def perform_transaction(queries):
    try:
        for query in queries:
            db.session.execute(query)
        db.session.commit()
    except Exception as e:
        logging.error(f"Transaction failed: {e}")
        db.session.rollback()
