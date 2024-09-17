import logging
import re
from models.gpt2_observer import gpt2_restructure_prompt
from .file_operations import write_file, read_file
from .code_execution import (
    execute_code,
    create_folder,
    delete_folder,
    create_file,
    delete_file,
    extract_name_from_message,
    extract_code_from_message
)

logging.basicConfig(level=logging.DEBUG)

def parse_intent_with_gpt2(message):
    """Use GPT-2 to analyze the message and determine if an action is required."""
    restructured_message = gpt2_restructure_prompt(message)

    if "create" in restructured_message.lower() and "folder" in restructured_message.lower():
        return "create_folder"
    if "delete" in restructured_message.lower() and "file" in restructured_message.lower():
        return "delete_file"
    # Additional command checks

    return "api_request"  # Default to API request if no action is identified

def parse_intent(message):
    """Parse the message to check if it should trigger tool usage."""
    logging.debug(f"Parsing intent for message: {message.lower()}")

    # Check for file management commands with more dynamic handling
    if re.search(r'create folder\s+"(.*?)"', message.lower()):
        return "create_folder"
    if re.search(r'delete folder\s+"(.*?)"', message.lower()):
        return "delete_folder"
    if re.search(r'create file\s+"(.*?)"', message.lower()):
        return "create_file"
    if re.search(r'delete file\s+"(.*?)"', message.lower()):
        return "delete_file"

    # Check for code execution commands, including specifying language
    if "execute python code" in message.lower():
        return "execute_python_code"
    if "execute bash code" in message.lower():
        return "execute_bash_code"
    if "execute javascript code" in message.lower():
        return "execute_js_code"

    # Fallback to default API request for unrecognized commands
    return "api_request"

def handle_task(intent, message):
    past_interactions = retrieve_memory(session.get('user_id'), session_id=session.get('session_id'), task_type=intent)
    if past_interactions and past_interactions[-1].task_outcome == "failure":
        return "Previous task failed, adjusting approach."
    # Execute original task logic
    """Handle task based on GPT-2 inferred intent."""
    logging.debug(f"Handling task: {intent} with message: {message}")

    if intent == "create_folder":
        folder_name = extract_name_from_message(message)
        logging.debug(f"Creating folder: {folder_name}")
        return create_folder(folder_name)

    if intent == "delete_folder":
        folder_name = extract_name_from_message(message)
        logging.debug(f"Deleting folder: {folder_name}")
        return delete_folder(folder_name)

    if intent == "create_file":
        file_name = extract_name_from_message(message)
        logging.debug(f"Creating file: {file_name}")
        return create_file(file_name)

    if intent == "delete_file":
        file_name = extract_name_from_message(message)
        logging.debug(f"Deleting file: {file_name}")
        return delete_file(file_name)

    if intent == "execute_python_code":
        code = extract_code_from_message(message)
        logging.debug(f"Executing Python code: {code}")
        return execute_code(code, language='python')

    if intent == "execute_bash_code":
        code = extract_code_from_message(message)
        logging.debug(f"Executing Bash code: {code}")
        return execute_code(code, language='bash')

    if intent == "execute_js_code":
        code = extract_code_from_message(message)
        logging.debug(f"Executing JavaScript code: {code}")
        return execute_code(code, language='javascript')

    return "Unknown intent."

def extract_name_from_message(message):
    """Extract file or folder name from the message."""
    match = re.search(r'\"(.*?)\"', message)
    return match.group(1) if match else "Untitled"

def extract_code_from_message(message):
    """Extract code from message."""
    match = re.search(r"```(.*?)```", message, re.DOTALL)
    return match.group(1) if match else message
