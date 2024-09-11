import subprocess
import os
from tools.task_logging import log_task_result

def extract_name_from_message(message):
    """Extract file or folder name from the message."""
    match = re.search(r'\"(.*?)\"', message)
    return match.group(1) if match else "Untitled"  # Fallback to "Untitled" if no match is found

def extract_code_from_message(message):
    """Extract code from message."""
    match = re.search(r"```(.*?)```", message, re.DOTALL)
    return match.group(1) if match else message  # Fallback to the entire message if no code block is found

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

def extract_code_from_response(response):
    """
    Extract code block from the API response.
    Modify as needed for various languages.
    """
    code_block = response.get('choices', [{}])[0].get('message', {}).get('content', '')
    return code_block

def execute_code(code):
    """
    Executes the extracted Python code in a secure environment.
    """
    try:
        result = subprocess.run(['python3', '-c', code], capture_output=True, text=True, timeout=10)
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
        result = subprocess.run(bash_command, capture_output=True, text=True, shell=True, timeout=10)
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
        result = subprocess.run(['node', '-e', js_code], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return {"status": "success", "output": result.stdout}
        else:
            return {"status": "error", "output": result.stderr}
    except subprocess.TimeoutExpired:
        return {"status": "error", "output": "Execution timeout"}
    except Exception as e:
        return {"status": "error", "output": str(e)}

def handle_code_execution(api_response):
    """
    Handles code execution from the API response.
    """
    # Extract the code
    code = extract_code_from_response(api_response)
    
    # Execute the code and log the result
    execution_result = execute_code(code)
    
    # Log the result (whether success or failure)
    log_task_result(api_response, execution_result)
    
    return execution_result
