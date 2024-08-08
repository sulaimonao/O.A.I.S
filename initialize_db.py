import sqlite3
import logging

def initialize_database():
    try:
        connection = sqlite3.connect('your_database.db')
        cursor = connection.cursor()
        with open('schema.sql', 'r') as file:
            schema = file.read()
        cursor.executescript(schema)
        connection.commit()
    except (sqlite3.DatabaseError, FileNotFoundError) as e:
        logging.error(f"Database initialization failed: {e}")
    finally:
        connection.close()

if __name__ == '__main__':
    initialize_database()
