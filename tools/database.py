import sqlite3
from contextlib import closing
import os

DATABASE = 'conversation.db'

def init_db():
    if os.path.exists(DATABASE):
        user_input = input("Database already exists. Do you want to create a new one? (yes/no): ").strip().lower()
        if user_input == 'yes':
            os.remove(DATABASE)
            create_db()
        else:
            print("Using existing database.")
    else:
        create_db()

def create_db():
    with closing(sqlite3.connect(DATABASE)) as db:
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    with closing(sqlite3.connect(DATABASE)) as db:
        cur = db.execute(query, args)
        rv = cur.fetchall()
        db.commit()
        return (rv[0] if rv else None) if one else rv

def add_message(session_id, user_id, role, content, model):
    query_db(
        'INSERT INTO messages (session_id, user_id, role, content, model) VALUES (?, ?, ?, ?, ?)',
        [session_id, user_id, role, content, model]
    )

def get_conversation_history(session_id):
    return query_db(
        'SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp',
        [session_id]
    )
