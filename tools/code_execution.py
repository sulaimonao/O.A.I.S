import os
import subprocess
import logging
import uuid
from contextlib import contextmanager

venv_dir = 'shared_venv'
workspace_dir = 'virtual_workspace'

os.makedirs(venv_dir, exist_ok=True)
os.makedirs(workspace_dir, exist_ok=True)

@contextmanager
def setup_virtualenv():
    venv_activated = os.path.join(venv_dir, 'bin', 'activate')
    if not os.path.exists(venv_activated):
        logging.info(f"Creating shared virtual environment at {venv_dir}")
        subprocess.run(['python3', '-m', 'venv', venv_dir], check=True)
    yield

def install_packages(packages):
    if packages:
        logging.info(f"Installing packages: {', '.join(packages)}")
        pip_path = os.path.join(venv_dir, 'bin', 'pip')
        try:
            subprocess.run(
                [pip_path, 'install'] + packages,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing packages: {e.stderr}")
            raise

def execute_code(code):
    with setup_virtualenv():
        env_path = venv_dir
        python_executable = os.path.join(env_path, 'bin', 'python')
        exec_script = os.path.join(workspace_dir, f'exec_code_{uuid.uuid4().hex}.py')

        with open(exec_script, 'w') as f:
            f.write(code)

        install_packages(['matplotlib', 'numpy'])

        try:
            result = subprocess.run(
                [python_executable, exec_script],
                check=True,
                capture_output=True,
                text=True
            )
            logging.debug(f"Execution result: {result.stdout}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logging.error(f"Error during code execution: {e.stderr}")
            return e.stderr

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        return f"Folder '{folder_name}' created."
    return f"Folder '{folder_name}' already exists."

def delete_folder(folder_name):
    if os.path.exists(folder_name):
        os.rmdir(folder_name)
        return f"Folder '{folder_name}' deleted."
    return f"Folder '{folder_name}' does not exist."

def create_file(file_name, content=""):
    file_path = os.path.join(workspace_dir, file_name)
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        return f"File '{file_name}' created with content."
    except Exception as e:
        logging.error(f"Error creating file '{file_name}': {e}")
        return f"Error creating file '{file_name}'."

def delete_file(file_name):
    file_path = os.path.join(workspace_dir, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        return f"File '{file_name}' deleted."
    return f"File '{file_name}' does not exist."

def execute_bash_code(code):
    exec_script = os.path.join(workspace_dir, f'exec_code_{uuid.uuid4().hex}.sh')

    with open(exec_script, 'w') as f:
        f.write(code)

    try:
        result = subprocess.run(
            ['bash', exec_script],
            check=True,
            capture_output=True,
            text=True
        )
        logging.debug(f"Execution result: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during bash code execution: {e.stderr}")
        return e.stderr

def execute_js_code(code):
    exec_script = os.path.join(workspace_dir, f'exec_code_{uuid.uuid4().hex}.js')

    with open(exec_script, 'w') as f:
        f.write(code)

    try:
        result = subprocess.run(
            ['node', exec_script],
            check=True,
            capture_output=True,
            text=True
        )
        logging.debug(f"Execution result: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during JavaScript code execution: {e.stderr}")
        return e.stderr
