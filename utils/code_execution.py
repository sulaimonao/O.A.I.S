import os
import subprocess
import logging
import uuid
from utils.file_operations import write_file

# Define the path to the shared virtual environment
venv_dir = 'shared_venv'
workspace_dir = 'virtual_workspace'

# Ensure that the virtual environment and workspace directories exist
os.makedirs(venv_dir, exist_ok=True)
os.makedirs(workspace_dir, exist_ok=True)

def setup_virtualenv():
    """Set up a shared virtual environment if it doesn't exist."""
    if not os.path.exists(os.path.join(venv_dir, 'bin', 'activate')):
        logging.info(f"Creating shared virtual environment at {venv_dir}")
        subprocess.run(['python3', '-m', 'venv', venv_dir], check=True)
    else:
        logging.info(f"Using existing virtual environment at {venv_dir}")

def install_packages(packages):
    """Install required packages into the shared virtual environment."""
    if packages:
        logging.info(f"Installing packages: {', '.join(packages)}")
        activate_script = os.path.join(venv_dir, 'bin', 'activate')
        try:
            subprocess.run(
                f"source {activate_script} && pip install {' '.join(packages)}",
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing packages: {e.stderr}")
            raise

def execute_code(code, additional_packages=None):
    """Execute the provided code in the shared virtual environment."""
    additional_packages = additional_packages or []
    setup_virtualenv()  # Ensure virtual environment is set up

    # Install required packages including additional ones if any
    install_packages(['matplotlib', 'numpy'] + additional_packages)

    # Generate a dynamic filename using UUID
    exec_script_name = f"exec_code_{uuid.uuid4()}.py"
    exec_script_path = os.path.join(workspace_dir, exec_script_name)

    # Write the code to a Python script using write_file function
    result = write_file(exec_script_path, code)
    if "successfully" not in result:
        return f"Error writing to file: {result}"

    # Run the script in the shared virtual environment
    activate_script = os.path.join(venv_dir, 'bin', 'activate')
    try:
        result = subprocess.run(
            f"source {activate_script} && python {exec_script_path}",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        logging.debug(f"Execution result: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during code execution: {e.stderr}")
        return e.stderr
