import logging
import re
from .file_operations import write_file
from .code_execution import execute_code, execute_bash_code, execute_js_code

logging.basicConfig(level=logging.DEBUG)

def parse_intent(message):
    """Parse the message to check if it should trigger tool usage."""
    logging.debug(f"Parsing intent for message: {message.lower()}")

    # Check if the message contains tool-related keywords
    if any(keyword in message.lower() for keyword in ["write to file", "create to file", "save a file"]):
        return "write_to_file"
    if "write/execute" in message.lower() or "run code" in message.lower() or "execute code" in message.lower():
        return "execute_code"

    # If no tool-related keywords, return 'api_request' for normal API processing
    return "api_request"

def handle_write_to_file(message, content):
    filename = "output"
    extension = ".txt"

    if "poem" in message.lower():
        filename = "poem"
    elif "song" in message.lower():
        filename = "song"
    elif "text" in message.lower():
        filename = "text"
    elif "image" in message.lower():
        filename = "image"
        extension = ".png"  # Placeholder, should be image processing logic
    elif "audio" in message.lower():
        filename = "audio"
        extension = ".mp3"  # Placeholder, should be audio processing logic
    elif "data" in message.lower():
        filename = "data"
        extension = ".csv"  # Placeholder, should be data processing logic

    full_filename = f"{filename}{extension}"
    result = write_file(full_filename, content)
    logging.debug(f"Content written to file: {full_filename}, Result: {result}")
    return f"Content has been written to {full_filename}"

def handle_execute_code(message, generated_code):
    """Handles execution of Python, Bash, and JavaScript code."""
    match = re.search(r"```(\w+)\s+(.*?)\s+```", generated_code, re.DOTALL)
    if match:
        language = match.group(1).lower()
        code = match.group(2)
    else:
        language = "text"
        code = generated_code.strip('```').strip()

    # Dispatch table for different language code executions
    language_execution = {
        "python": execute_code,
        "bash": execute_bash_code,
        "javascript": execute_js_code
    }

    if language in language_execution:
        result = language_execution[language](code)
    else:
        result = f"Code in {language} language saved to output.txt"
        write_file(f"output.txt", code)

    logging.debug(f"Code execution result: {result}")
    return result
