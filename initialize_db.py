import sqlite3

def initialize_database():
    connection = sqlite3.connect('your_database.db')
    cursor = connection.cursor()

    with open('schema.sql', 'r') as file:
        schema = file.read()
    
    cursor.executescript(schema)
    connection.commit()
    connection.close()

if __name__ == '__main__':
    initialize_database()
