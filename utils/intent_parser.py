#intent_parser.py
#can handle different intents like writing to a file, reading from a file, executing code, interacting with hardware, and executing OS commands. This version assumes that the actual execution logic (like file operations, code execution) is handled by dedicated functions that are imported and called based on the detected intent.
import logging
import re
import spacy
from utils.file_operations import write_file, read_file  # Assuming these are your custom utilities
from utils.code_execution import execute_code  # Assuming this is your custom utility for executing code
import time
import os
import uuid
import subprocess

# Load spaCy's English language model for intent parsing
nlp = spacy.load("en_core_web_sm")

WORKSPACE_DIR = "virtual_workspace"

def get_workspace_path():
    if not os.path.exists(WORKSPACE_DIR):
        os.makedirs(WORKSPACE_DIR)
    return WORKSPACE_DIR

def generate_unique_filename(extension=".py"):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    unique_id = str(uuid.uuid4())
    return f"script_{timestamp}_{unique_id}{extension}"

def parse_intent(message):
    """
    Parse the intent from the user's message.
    """
    logging.debug(f"Parsing intent for message: {message.lower()}")
    doc = nlp(message.lower())

    # Define keywords that trigger different intents
    intents = {
        "write_to_file": ["write to file", "create file", "save to file"],
        "read_from_file": ["read file", "open file", "load file"],
        "execute_code": ["execute code", "run code", "generate and execute"],
        "hardware_interaction": ["turn on", "turn off", "activate", "deactivate"],
        "execute_os_command": ["run command", "execute command", "system command"]
    }

    for intent, keywords in intents.items():
        if any(kw in message.lower() for kw in keywords):
            logging.debug(f"Intent identified: {intent}")
            return intent

    logging.debug("No matching intent found")
    return "unknown"

def handle_write_to_file(message, content):
    """
    Handle writing content to a file based on user intent.
    """
    # Determine the filename and extension based on the message content
    filename = generate_unique_filename(extension=".txt")
    if "poem" in message.lower():
        filename = generate_unique_filename(extension=".txt")
    elif "data" in message.lower():
        filename = generate_unique_filename(extension=".csv")

    # Write the content to the file
    result = write_file(filename, content)
    logging.debug(f"Content written to file: {filename}, Result: {result}")
    return f"Content has been written to {filename}"

def handle_read_from_file(message):
    """
    Handle reading content from a file based on user intent.
    """
    # Determine the filename based on the message content
    filename = "output.txt"
    if "poem" in message.lower():
        filename = "poem.txt"
    elif "data" in message.lower():
        filename = "data.csv"

    # Read the content from the file
    content = read_file(filename)
    logging.debug(f"Content read from file: {filename}, Content: {content}")
    return content

def extract_python_code(generated_response):
    """
    Extract Python code from the LLM's generated response using regex.
    """
    match = re.search(r"```python(.*?)```", generated_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def handle_execute_code(message, generated_response):
    """
    Handle the execution of Python code extracted from the LLM response.
    """
    code = extract_python_code(generated_response)
    
    if code:
        workspace_path = get_workspace_path()
        filename = generate_unique_filename()

        # Save the code to a file within the workspace
        file_path = os.path.join(workspace_path, filename)
        with open(file_path, "w") as f:
            f.write(code)
        
        logging.debug(f"Saved code to {file_path}")

        try:
            # Execute the Python code and capture the output
            result = subprocess.check_output(["python3", file_path], stderr=subprocess.STDOUT)
            result = result.decode('utf-8')
            logging.debug(f"Code executed successfully: {result}")
            return f"Code executed successfully:\n{result}"
        except subprocess.CalledProcessError as e:
            error_output = e.output.decode('utf-8')
            logging.error(f"Error executing code at {file_path}: {error_output}")
            return f"Error executing code:\n{error_output}"
    else:
        logging.warning("No valid Python code found in the response.")
        return "Failed to find valid Python code in the response."

def handle_hardware_interaction(message):
    """
    Handle hardware interaction requests based on user intent.
    This function is a placeholder for actual hardware control logic.
    """
    logging.debug(f"Handling hardware interaction for message: {message.lower()}")
    return "Hardware interaction not implemented yet."

def handle_execute_os_command(message):
    """
    Handle OS command execution based on user intent.
    This function is a placeholder for actual OS command execution logic.
    """
    logging.debug(f"Executing OS command for message: {message.lower()}")
    return "OS command execution not implemented yet."
