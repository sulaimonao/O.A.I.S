import os

workspace_dir = 'virtual_workspace'

# Ensure the workspace directory exists
os.makedirs(workspace_dir, exist_ok=True)

def read_file(file_path):
    try:
        with open(os.path.join(workspace_dir, file_path), 'r') as file:
            return file.read()
    except Exception as e:
        return str(e)

def write_file(file_path, content):
    try:
        with open(os.path.join(workspace_dir, file_path), 'w') as file:
            file.write(content)
        return "File written successfully"
    except Exception as e:
        return str(e)
