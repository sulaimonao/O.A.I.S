import os
import json
import threading
from queue import Queue

def extract_file_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            # Example of selective content extraction (modify as needed)
            content = ''.join(line for line in file if 'def' in line or 'class' in line)
            return {
                'file_name': os.path.basename(file_path),
                'path': file_path,
                'content': content
            }
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def worker(file_queue, data_list):
    while not file_queue.empty():
        file_path = file_queue.get()
        file_data = extract_file_data(file_path)
        if file_data:
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
folder_path = '/Users/akeemsulaimon/O.A.I.S.'
output_json_file = 'memory_database.json'
file_extensions = ['.py', '.txt', '.cc', '.xcode', '.xcodeproj', '.xcworkspace', '.swift', '.dart', '.plist', '.xcconfig', '.js', '.md', '.ipynb', '.mindnode', '.cs', '.cpp', '.css', '.html']  # Add or remove extensions as needed

create_database_from_files(folder_path, output_json_file, file_extensions)
