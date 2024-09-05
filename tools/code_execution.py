import os
import subprocess
import logging
import uuid
from contextlib import contextmanager

# Define the path to the shared virtual environment
venv_dir = 'shared_venv'
workspace_dir = 'virtual_workspace'

# Ensure that the virtual environment and workspace directories exist
os.makedirs(venv_dir, exist_ok=True)
os.makedirs(workspace_dir, exist_ok=True)

@contextmanager
def setup_virtualenv():
    """Set up a shared virtual environment if it doesn't exist."""
    if not os.path.exists(os.path.join(venv_dir, 'bin', 'activate')):
        logging.info(f"Creating shared virtual environment at {venv_dir}")
        subprocess.run(['python3', '-m', 'venv', venv_dir], check=True)
    else:
        logging.info(f"Using existing virtual environment at {venv_dir}")
    try:
        yield
    finally:
        # Clean-up actions can go here if needed
        pass

def install_packages(packages):
    """Install required packages into the shared virtual environment."""
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
    """Execute Python code inside the shared virtual environment."""
    with setup_virtualenv():
        env_path = venv_dir
        python_executable = os.path.join(env_path, 'bin', 'python')
        exec_script = os.path.join(workspace_dir, f'exec_code_{uuid.uuid4().hex}.py')

        # Write the code to a Python script
        with open(exec_script, 'w') as f:
            f.write(code)

        # Install required packages before running the script
        install_packages(['matplotlib', 'numpy'])

        # Run the script in the virtual environment
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
