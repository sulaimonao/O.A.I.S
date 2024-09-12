#This file logs the success or failure of tasks and stores them in a database using SQLAlchemy.
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_input = db.Column(db.String(500))
    intent = db.Column(db.String(50))
    success = db.Column(db.Boolean)

def log_task(user_input, intent, success):
    new_task = TaskHistory(user_input=user_input, intent=intent, success=success)
    db.session.add(new_task)
    db.session.commit()

def log_task_result(api_response, result):
    with open("logs/task_logs.txt", "a") as log_file:
        log_file.write(f"API Response: {api_response}\n")
        log_file.write(f"Execution Result: {result}\n")
