import os
import re
import logging
from utils.code_execution import execute_code  # Import execute_code function
from utils.file_operations import write_file, read_file

workspace_dir = 'virtual_workspace'

def get_workspace_path():
    """Get the path to the workspace."""
    return workspace_dir

def generate_unique_filename(extension=".py"):
    """Generate a unique filename using UUID."""
    return f"code_{uuid.uuid4()}{extension}"

def parse_intent(message):
    """Parse the intent from the user's message."""
    if "write to file" in message.lower():
        return "write_to_file"
    elif "execute code" in message.lower():
        return "execute_code"
    return None

def handle_write_to_file(message, content):
    """Handle saving content to a file."""
    filename = generate_unique_filename()
    file_path = os.path.join(get_workspace_path(), filename)
    
    result = write_file(file_path, content)
    if "successfully" in result:
        logging.debug(f"Saved content to {file_path}")
        return f"Content written to {file_path}"
    else:
        logging.error(f"Error writing to file {file_path}: {result}")
        return result

def extract_python_code(generated_response):
    """Extract Python code from the LLM response."""
    match = re.search(r'```python(.*?)```', generated_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def handle_execute_code(message, generated_response):
    """Handle the execution of Python code extracted from the LLM response."""
    code = extract_python_code(generated_response)
    
    if code:
        # Execute the code using the shared virtual environment
        result = execute_code(code)
        return result
    else:
        logging.warning("No valid Python code found in the response.")
        return "Failed to find valid Python code in the response."

def handle_hardware_interaction(message):
    """Handle hardware interaction requests based on user intent."""
    logging.debug(f"Handling hardware interaction for message: {message.lower()}")
    return "Hardware interaction not implemented yet."

def handle_execute_os_command(message):
    """Handle OS command execution based on user intent."""
    logging.debug(f"Executing OS command for message: {message.lower()}")
    return "OS command execution not implemented yet."
