# backend/tools/task_logging.py

from backend.models.models import CodeExecutionLog, TaskHistory  # Corrected import
from datetime import datetime
from backend.models.db import db
import logging


# Logging task functions

def log_task(user_input, intent, success):
    """
    Logs a generic task performed by the user.
    """
    task_history = TaskHistory(
        user_input=user_input,
        intent=intent,
        success=success,
        timestamp=datetime.utcnow()
    )
    db.session.add(task_history)
    db.session.commit()
    logging.info(f"Logged task: {intent} with success status: {success}")

def log_task_result(api_response, result):
    with open("logs/task_logs.txt", "a") as log_file:
        log_file.write(f"API Response: {api_response}\n")
        log_file.write(f"Execution Result: {result}\n")

def log_task_execution(user_id, task_type, input_code, output, status):
    """
    Logs the execution of code or tasks performed by the user.
    """
    execution_log = CodeExecutionLog(
        user_id=user_id,
        task_type=task_type,
        input_code=input_code,
        output=output,
        status=status,
        timestamp=datetime.utcnow()
    )
    db.session.add(execution_log)
    db.session.commit()
    logging.info(f"Logged execution: {task_type} with status: {status}")
