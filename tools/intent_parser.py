import logging
import re
from .file_operations import write_file
from .code_execution import execute_code

logging.basicConfig(level=logging.DEBUG)

def parse_intent(message):
    logging.debug(f"Parsing intent for message: {message.lower()}")

    if any(keyword in message.lower() for keyword in ["write to file", "create to file", "save a file"]):
        return "write_to_file"
    if "write/execute" in message.lower() or "generate code" in message.lower():
        return "execute_code"

    return "unknown"

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
    # Detect the language and clean the code
    match = re.search(r"```(\w+)\s+(.*?)\s+```", generated_code, re.DOTALL)
    if match:
        language = match.group(1)
        code = match.group(2)
    else:
        language = "text"
        code = generated_code.strip('```').strip()

    # Determine the file extension based on the language
    extension = {
        "python": ".py",
        "bash": ".sh",
        "javascript": ".js",
        "text": ".txt"
    }.get(language, ".txt")

    filename = f"output{extension}"

    # Execute the code if it's a Python script
    if language == "python":
        result = execute_code(code)
        logging.debug(f"Python code executed. Result: {result}")
    else:
        result = f"Code in {language} language saved to {filename}"

    # Write the cleaned code to a file
    write_file(filename, code)
    logging.debug(f"Code written to file: {filename}")
    return result
