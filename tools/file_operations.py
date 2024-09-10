import os
import logging

workspace_dir = 'virtual_workspace'

# Ensure the workspace directory exists
os.makedirs(workspace_dir, exist_ok=True)

def read_file(file_path):
    try:
        full_path = os.path.join(workspace_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"{file_path} does not exist.")
        
        with open(full_path, 'r') as file:
            return file.read()
    except FileNotFoundError as fnf_error:
        logging.error(fnf_error)
        return str(fnf_error)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return str(e)

def write_file(file_path, content):
    try:
        with open(os.path.join(workspace_dir, file_path), 'w') as file:
            file.write(content)
        logging.info(f"File written successfully to {file_path}")
        return "File written successfully"
    except Exception as e:
        logging.error(f"Error writing to file {file_path}: {e}")
        return str(e)
