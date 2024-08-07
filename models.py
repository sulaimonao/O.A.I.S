import sqlite3
from contextlib import closing
import os
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
DATABASE = Config.DATABASE

def init_db():
    try:
        if os.path.exists(DATABASE):
            logging.info("Using existing database.")
        else:
            create_db()
            logging.info("Database created successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")

def create_db():
    try:
        with closing(sqlite3.connect(DATABASE)) as db:
            with open('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()
    except Exception as e:
        logging.error(f"Failed to create database: {e}")

def query_db(query, args=(), one=False):
    try:
        with closing(sqlite3.connect(DATABASE)) as db:
            cur = db.execute(query, args)
            rv = cur.fetchall()
            db.commit()
            return (rv[0] if rv else None) if one else rv
    except Exception as e:
        logging.error(f"Database query failed: {e}")
        return None

def add_message(session_id, user_id, role, content, model):
    try:
        query_db(
            'INSERT INTO messages (session_id, user_id, role, content, model) VALUES (?, ?, ?, ?, ?)',
            [session_id, user_id, role, content, model]
        )
    except Exception as e:
        logging.error(f"Failed to add message: {e}")

# Other functions remain the same with added error handling and logging.
