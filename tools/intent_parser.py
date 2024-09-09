import logging
import re
from .file_operations import write_file
from .code_execution import execute_code, execute_bash_code, execute_js_code

logging.basicConfig(level=logging.DEBUG)

def parse_intent(message):
    logging.debug(f"Parsing intent for message: {message.lower()}")

    if any(keyword in message.lower() for keyword in ["write to file", "create to file", "save a file"]):
        return "write_to_file"
    if "write/execute" in message.lower() or "run code" in message.lower() or "execute code" in message.lower():
        return "execute_code"
    if "generate code" in message.lower() or "create code" in message.lower():
        return "generate_code"

    return "unknown"

def handle_execute_code(message, generated_code):
    # Detect the language and extract code from the generated response
    match = re.search(r"```(\w+)\s+(.*?)\s+```", generated_code, re.DOTALL)
    if match:
        language = match.group(1).lower()
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

    # Execute the code based on the detected language
    if language == "python":
        result = execute_code(code)
    elif language == "bash":
        result = execute_bash_code(code)
    elif language == "javascript":
        result = execute_js_code(code)
    else:
        result = f"Code in {language} language saved to {filename}"

    # Write the cleaned code to a file
    write_file(filename, code)
    logging.debug(f"Code written to file: {filename}")
    return result
