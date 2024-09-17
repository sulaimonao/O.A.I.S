from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()  # Initialize the SQLAlchemy object

class CodeExecutionLog(db.Model):
    __tablename__ = 'code_execution_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    language = db.Column(db.String, nullable=False)
    code = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text, nullable=True)
    status = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CodeExecutionLog {self.id} - User {self.user_id}>"

class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_input = db.Column(db.String(500))
    intent = db.Column(db.String(50))
    success = db.Column(db.Boolean)

    def __repr__(self):
        return f"<TaskHistory {self.id} - Intent {self.intent}>"

# Logging task functions

def log_task(user_input, intent, success):
    new_task = TaskHistory(user_input=user_input, intent=intent, success=success)
    db.session.add(new_task)
    db.session.commit()

def log_task_result(api_response, result):
    with open("logs/task_logs.txt", "a") as log_file:
        log_file.write(f"API Response: {api_response}\n")
        log_file.write(f"Execution Result: {result}\n")

def log_task_execution(user_id, task_type, input_code, output, status):
    code_log = CodeExecutionLog(
        user_id=user_id,
        language=task_type,  # Change language as needed
        code=input_code,
        output=output,
        status=status,
        timestamp=datetime.utcnow()
    )
    db.session.add(code_log)
    db.session.commit()
