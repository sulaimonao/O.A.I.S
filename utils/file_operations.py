import os
import uuid
from flask import request, jsonify

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

def upload_files():
    if 'files[]' not in request.files:
        return jsonify(error="No files part"), 400

    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    upload_dir = os.path.join(workspace_dir, str(uuid.uuid4()))
    os.makedirs(upload_dir, exist_ok=True)

    filenames = []
    for file in files:
        if file:
            file_path = os.path.join(upload_dir, file.filename)
            file.save(file_path)
            filenames.append(file.filename)

    return jsonify(filenames=filenames, folder=upload_dir)
