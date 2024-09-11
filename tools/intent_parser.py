import logging
import re
from .file_operations import write_file
from .code_execution import (
    execute_code,
    execute_bash_code,
    execute_js_code,
    create_folder,
    delete_folder,
    create_file,
    delete_file
)

logging.basicConfig(level=logging.DEBUG)

def parse_intent(message):
    """Parse the message to check if it should trigger tool usage."""
    logging.debug(f"Parsing intent for message: {message.lower()}")

    # Check for folder/file management commands
    if "create folder" in message.lower():
        return "create_folder"
    if "delete folder" in message.lower():
        return "delete_folder"
    if "create file" in message.lower():
        return "create_file"
    if "delete file" in message.lower():
        return "delete_file"

    # Check for code execution
    if "run code" in message.lower() or "execute code" in message.lower():
        return "execute_code"

    # If no tool-related keywords, return 'api_request' for normal API processing
    return "api_request"

def handle_task(intent, message):
    """Handle task based on intent."""
    if intent == "create_folder":
        folder_name = extract_name_from_message(message)
        return create_folder(folder_name)

    if intent == "delete_folder":
        folder_name = extract_name_from_message(message)
        return delete_folder(folder_name)

    if intent == "create_file":
        file_name = extract_name_from_message(message)
        return create_file(file_name)

    if intent == "delete_file":
        file_name = extract_name_from_message(message)
        return delete_file(file_name)

    if intent == "execute_code":
        code = extract_code_from_message(message)
        return execute_code(code)

    return "Invalid intent."

def extract_name_from_message(message):
    """Extract file or folder name from the message (basic extraction for now)."""
    match = re.search(r'\"(.*?)\"', message)
    if match:
        return match.group(1)
    return "Untitled"

def extract_code_from_message(message):
    """Extract code from message."""
    match = re.search(r"```(.*?)```", message, re.DOTALL)
    if match:
        return match.group(1)
    return message
