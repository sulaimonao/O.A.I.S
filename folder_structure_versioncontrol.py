import os
import json
import threading
from queue import Queue
from datetime import datetime
import subprocess
import re

def extract_file_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
            functions = [line.strip() for line in lines if line.strip().startswith('def ')]
            classes = [line.strip() for line in lines if line.strip().startswith('class ')]
            content = ''.join(lines)
            return {
                'file_name': os.path.basename(file_path),
                'path': file_path,
                'functions': functions,
                'classes': classes,
                'content': content
            }
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def get_git_history(file_path):
    try:
        result = subprocess.run(['git', 'log', '--pretty=format:%H %an %ad %s', '--', file_path],
                                capture_output=True, text=True, check=True)
        history = []
        log_pattern = re.compile(r'([a-f0-9]+) (.+?) (.+?) (.+)')
        for line in result.stdout.split('\n'):
            match = log_pattern.match(line)
            if match:
                commit_hash, author, date, message = match.groups()
                history.append({
                    'commit_hash': commit_hash,
                    'author': author,
                    'date': date,
                    'message': message
                })
        return history
    except Exception as e:
        print(f"Error retrieving git history for {file_path}: {e}")
        return []

def worker(file_queue, data_list):
    while not file_queue.empty():
        file_path = file_queue.get()
        file_data = extract_file_data(file_path)
        if file_data:
            file_data['history'] = get_git_history(file_path)
            data_list.append(file_data)
        file_queue.task_done()

def create_database_from_files(folder_path, output_file, extensions=None, num_threads=5):
    file_queue = Queue()
    data_list = []
    threads = []

    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d != '__pycache__']  # Ignore __pycache__ directories
        for file in files:
            if extensions and not any(file.endswith(ext) for ext in extensions):
                continue
            file_path = os.path.join(root, file)
            file_queue.put(file_path)

    for _ in range(num_threads):
        thread = threading.Thread(target=worker, args=(file_queue, data_list))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, indent=4)

# Example usage
folder_path = '/Users/akeemsulaimon/Documents/GitHub/O.A.I.S'
output_json_file = 'memory_database.json'
file_extensions = ['.py', '.txt', '.cc', '.xcode', '.xcodeproj', '.xcworkspace', '.swift', '.dart', '.plist', '.xcconfig', '.js', '.md', '.ipynb', '.mindnode', '.cs', '.cpp', '.css', '.html']  # Add or remove extensions as needed

create_database_from_files(folder_path, output_json_file, file_extensions)
