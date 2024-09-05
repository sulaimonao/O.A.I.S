import os
import subprocess
import logging
import uuid
from contextlib import contextmanager

@contextmanager
def virtualenv(name):
    env_path = os.path.join('virtual_workspace', name)
    try:
        logging.info(f"Creating virtual environment at {env_path}")
        subprocess.run(['python3', '-m', 'venv', env_path], check=True)
        yield env_path
    finally:
        logging.info(f"Cleaning up virtual environment at {env_path}")
        # Commenting out this line will prevent the deletion of the virtual environment and files
        #subprocess.run(['rm', '-rf', env_path])
        pass # Do nothing to preserve the environment and files

def execute_code(code, additional_packages=None):
    additional_packages = additional_packages or []
    env_name = str(uuid.uuid4())
    with virtualenv(env_name) as env_path:
        activate_script = os.path.join(env_path, 'bin', 'activate')
        exec_script = os.path.join(env_path, 'exec_code.py')
        with open(exec_script, 'w') as f:
            f.write(code)
        try:
            packages = ['matplotlib', 'numpy'] + additional_packages
            result = subprocess.run(
                f"source {activate_script} && pip install {' '.join(packages)} && python {exec_script}",
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            logging.info(f"Execution result: {result.stdout}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logging.error(f"Error during code execution: {e.stderr}")
            return e.stderr

