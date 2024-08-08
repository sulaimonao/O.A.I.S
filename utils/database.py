import sqlite3
from contextlib import closing
import os
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
DATABASE = Config.DATABASE

def init_db():
    logging.info("Initializing database...")
    try:
        if os.path.exists(DATABASE):
            logging.info("Using existing database.")
        else:
            create_db(DATABASE)
            logging.info("Database created successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")

def create_db(database_path):
    try:
        logging.info(f"Creating database at {database_path}...")
        with closing(sqlite3.connect(database_path)) as db:
            with open('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()
            logging.info("Database schema applied successfully.")
    except Exception as e:
        logging.error(f"Failed to create database: {e}")

def check_and_create_tables(database_path=DATABASE):
    try:
        logging.info(f"Checking and creating tables in {database_path} if they do not exist...")
        with closing(sqlite3.connect(database_path)) as db:
            schema = """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_profiles (
                session_id TEXT PRIMARY KEY,
                name TEXT,
                database_name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS chatroom_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
            db.cursor().executescript(schema)
            db.commit()
            logging.info(f"Tables checked and created in {database_path} if necessary.")
    except Exception as e:
        logging.error(f"Failed to check and create tables in {database_path}: {e}")

def query_db(query, args=(), one=False, database_path=DATABASE):
    try:
        with closing(sqlite3.connect(database_path)) as db:
            cur = db.execute(query, args)
            rv = cur.fetchall()
            db.commit()
            return (rv[0] if rv else None) if one else rv
    except sqlite3.DatabaseError as e:
        logging.error(f"Database query failed in {database_path}: {e}")
        return None

def add_message(session_id, user_id, role, content, model_name):
    try:
        conn = sqlite3.connect(Config.DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (session_id, user_id, role, content, model)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user_id, role, content, model_name))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Database query failed in {Config.DATABASE}: {e}")

def add_long_term_memory(session_id, content, database_path=DATABASE):
    try:
        query_db(
            'INSERT INTO long_term_memory (session_id, content) VALUES (?, ?)',
            [session_id, content],
            database_path=database_path
        )
    except sqlite3.DatabaseError as e:
        logging.error(f"Failed to add long-term memory in {database_path}: {e}")

def add_chatroom_memory(session_id, content, database_path=DATABASE):
    try:
        query_db(
            'INSERT INTO chatroom_memory (session_id, content) VALUES (?, ?)',
            [session_id, content],
            database_path=database_path
        )
    except sqlite3.DatabaseError as e:
        logging.error(f"Failed to add chatroom memory in {database_path}: {e}")

def get_conversation_history(session_id, database_path=DATABASE):
    try:
        return query_db(
            'SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp',
            [session_id],
            database_path=database_path
        )
    except sqlite3.DatabaseError as e:
        logging.error(f"Failed to get conversation history in {database_path}: {e}")
        return []

def get_user_profile(session_id, database_path=DATABASE):
    try:
        return query_db(
            'SELECT name FROM user_profiles WHERE session_id = ?',
            [session_id],
            one=True,
            database_path=database_path
        )
    except sqlite3.DatabaseError as e:
        logging.error(f"Failed to get user profile in {database_path}: {e}")
        return None

def set_user_profile(session_id, name, database_path=DATABASE):
    try:
        query_db(
            'INSERT OR REPLACE INTO user_profiles (session_id, name) VALUES (?, ?)',
            [session_id, name],
            database_path=database_path
        )
    except sqlite3.DatabaseError as e:
        logging.error(f"Failed to set user profile in {database_path}: {e}")

def get_existing_profiles():
    profiles = []
    for file in os.listdir(Config.BASEDIR):
        if file.endswith("_database.db"):
            profile_name = file.replace("_database.db", "")
            profiles.append(profile_name)
    return profiles

def perform_transaction(queries, args, database_path=DATABASE):
    try:
        with closing(sqlite3.connect(database_path)) as db:
            cursor = db.cursor()
            for query, arg in zip(queries, args):
                cursor.execute(query, arg)
            db.commit()
    except sqlite3.DatabaseError as e:
        db.rollback()
        logging.error(f"Transaction failed in {database_path}: {e}")
