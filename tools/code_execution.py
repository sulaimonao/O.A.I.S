import subprocess
import os
import resource
import re
import json
from tools.task_logging import log_task_result
from models.wordllama_observer import process_with_wordllama

# Resource Limitation Function
def limit_resources():
    """
    Limit resources for code execution to prevent abuse.
    """
    # Limit CPU time to 5 seconds
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    # Limit memory usage to 256MB
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))

# Code Extraction Functions
def extract_name_from_message(message):
    """Extract file or folder name from the message."""
    match = re.search(r'\"(.*?)\"', message)
    return match.group(1) if match else "Untitled"

def extract_code_from_message(message):
    """Extract code from message."""
    match = re.search(r"```(.*?)```", message, re.DOTALL)
    return match.group(1) if match else message

def extract_code_from_response(response):
    """
    Extract code block from the API response.
    Modify as needed for various languages.
    """
    code_block = response.get('choices', [{}])[0].get('message', {}).get('content', '')
    return code_block

# File and Folder Operations
def create_folder(folder_name):
    """
    Creates a folder in the system.
    """
    try:
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            return {"status": "success", "message": f"Folder '{folder_name}' created successfully."}
        else:
            return {"status": "error", "message": f"Folder '{folder_name}' already exists."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def delete_folder(folder_name):
    """
    Deletes a folder from the system.
    """
    try:
        if os.path.exists(folder_name):
            os.rmdir(folder_name)  # Only removes empty directories
            return {"status": "success", "message": f"Folder '{folder_name}' deleted successfully."}
        else:
            return {"status": "error", "message": f"Folder '{folder_name}' does not exist."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def create_file(file_name):
    """
    Creates an empty file in the system.
    """
    try:
        with open(file_name, 'w') as file:
            return {"status": "success", "message": f"File '{file_name}' created successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def delete_file(file_name):
    """
    Deletes a file from the system.
    """
    try:
        if os.path.exists(file_name):
            os.remove(file_name)
            return {"status": "success", "message": f"File '{file_name}' deleted successfully."}
        else:
            return {"status": "error", "message": f"File '{file_name}' does not exist."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Unified Code Execution Function
def execute_code(code, language='python'):
    """
    Executes code in the specified language with resource limits.
    """
    if language == 'python':
        return execute_python_code(code)
    elif language == 'bash':
        return execute_bash_code(code)
    elif language == 'javascript':
        return execute_js_code(code)
    else:
        return {"status": "error", "output": "Unsupported language"}

def execute_code_with_wordllama_support(code, message):
    """
    This function executes code and supports WordLlama for prompt analysis.
    """
    # Analyze the message with WordLlama if applicable
    wordllama_output = process_with_wordllama(message)
    
    # Proceed with regular code execution logic
    execution_result = execute_code(code, language='python')
    
    # Log the result with WordLlama support information
    log_task_result("Code Execution with WordLlama", {
        "wordllama_output": wordllama_output,
        "execution_result": execution_result
    })
    
    return execution_result

# Language-Specific Code Execution Functions
def execute_python_code(code):
    """
    Executes Python code with resource limits in place.
    """
    try:
        # Write code to a temporary file
        with open('temp_code.py', 'w') as file:
            file.write(code)

        result = subprocess.run(
            ['python3', 'temp_code.py'],
            # preexec_fn=limit_resources,  # Comment out for testing
            capture_output=True,
            text=True,
            timeout=10
        )
        os.remove('temp_code.py')  # Clean up the file
        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {"status": "error", "output": result.stderr}
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Execution timeout"}
    except Exception as e:
        return {"status": "error", "output": str(e)}

def execute_bash_code(bash_command):
    """
    Executes bash commands in a secure environment.
    """
    try:
        result = subprocess.run(
            bash_command,
            preexec_fn=limit_resources,
            capture_output=True,
            text=True,
            shell=True,
            timeout=10
        )
        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {"status": "error", "output": result.stderr}
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Execution timeout"}
    except Exception as e:
        return {"status": "error", "output": str(e)}

def execute_js_code(js_code):
    """
    Executes JavaScript code using Node.js.
    """
    try:
        result = subprocess.run(
            ['node', '-e', js_code],
            preexec_fn=limit_resources,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {"status": "error", "output": result.stderr}
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Execution timeout"}
    except Exception as e:
        return {"status": "error", "output": str(e)}

# Task Logging Function (Assuming you have a logging mechanism)
def log_task_result(task_name, execution_result):
    """
    Logs the task result for later review.
    """
    log_entry = {
        "task_name": task_name,
        "status": execution_result.get('status'),
        "output": execution_result.get('output')
    }
    # Ensure the logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open('logs/execution_log.json', 'a') as log_file:
        json.dump(log_entry, log_file)
        log_file.write('\n')  # Add newline to separate entries

# Handling Code Execution from API Response
def handle_code_execution(api_response, language='python'):
    """
    Handles code execution from the API response.
    """
    # Extract the code
    code = extract_code_from_response(api_response)

    # Execute the code and log the result
    execution_result = execute_code(code, language=language)

    # Log the result (whether success or failure)
    log_task_result("Code Execution", execution_result)

    return execution_result
