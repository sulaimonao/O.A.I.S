# backend/api/routes.py

from flask import Blueprint, render_template, request, jsonify, session
from backend.models.db import db
from backend.models.models import User, UserSession, Interaction, CodeExecutionLog
from backend.tools.memory import retrieve_memory
from backend.tools.code_execution import execute_python_code, execute_js_code, execute_bash_code
from backend.tools.intent_parser import parse_intent_with_gpt2, handle_task
from backend.tools.file_operations import read_file, write_file
from datetime import datetime
import logging
import os

api_bp = Blueprint('api', __name__)

@api_bp.route('/gpt2_interact', methods=['POST'])
def gpt2_interact():
    data = request.json
    input_text = data.get("input_text", "")
    if not input_text:
        return jsonify({"error": "No input text provided"}), 400

    try:
        session_id = session.get('session_id')
        past_interactions = retrieve_memory(session.get('user_id'), session_id)
        memory_prompt = input_text if not past_interactions else f"{input_text} {past_interactions[-1].prompt}"
        # GPT-2 interaction logic here
        # ...
        decoded_output = "Sample GPT-2 response"  # Replace with actual logic
        return jsonify({"response": decoded_output})
    except Exception as e:
        logging.error(f"Error generating GPT-2 response: {str(e)}")
        return jsonify({"error": f"Failed to generate GPT-2 response: {str(e)}"}), 500

@api_bp.route('/gpt2_status', methods=['GET'])
def gpt2_status():
    try:
        # GPT-2 status check logic here
        status = "operational"  # Replace with actual status check
        return jsonify({'status': status})
    except Exception as e:
        logging.error(f"Error loading GPT-2 model: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

@api_bp.route('/toggle_memory', methods=['POST'])
def toggle_memory():
    data = request.get_json()
    memory_enabled = data.get('memory_enabled')
    if memory_enabled is not None:
        session['memory_enabled'] = memory_enabled
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid memory status'}), 400

@api_bp.route('/get_profiles', methods=['GET'])
def get_profiles():
    users = User.query.all()
    profile_list = [{"id": user.id, "username": user.username} for user in users]
    return jsonify(profile_list)

@api_bp.route('/create_profile', methods=['POST'])
def create_profile():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Invalid username'}), 400

    user = init_user(username)
    if user:
        session['user_id'] = user.id
        return jsonify({'success': True, 'id': user.id})
    else:
        return jsonify({'error': 'Failed to create user profile. Please try again.'}), 500

@api_bp.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        upload_folder = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)
        return jsonify({'filename': file.filename})

@api_bp.route('/save_settings', methods=['POST'])
def save_settings():
    data = request.get_json()
    session['provider'] = data.get('provider', 'openai')
    session['model'] = data.get('model', 'gpt-4o')
    session['memory_enabled'] = data.get('memory_enabled', True)
    logging.debug(f"Settings saved: {session}")
    return jsonify({'success': True})

@api_bp.route('/get_settings', methods=['GET'])
def get_settings():
    provider = session.get('provider', 'openai')
    model = session.get('model', 'gpt-4o')
    memory_enabled = session.get('memory_enabled', True)
    logging.debug(f"Settings retrieved: Provider={provider}, Model={model}, Memory Enabled={memory_enabled}")
    return jsonify({
        'provider': provider,
        'model': model,
        'memory_enabled': memory_enabled
    })

@api_bp.route('/generate_gpt2', methods=['POST'])
def generate_gpt2():
    data = request.get_json()
    prompt = data.get('prompt', '')
    max_tokens = data.get('max_tokens', 100)

    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    # GPT-2 generation logic here
    response = "Sample GPT-2 generated text"  # Replace with actual logic
    return jsonify({'response': response})

@api_bp.route('/execute_code', methods=['POST'])
def execute_code_route():
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'python')

    if not code:
        return jsonify({'error': 'No code provided'}), 400

    user_id = session.get('user_id', 'anonymous')

    if language == 'python':
        result = execute_python_code(code)
    elif language == 'javascript':
        result = execute_js_code(code)
    elif language == 'bash':
        result = execute_bash_code(code)
    else:
        return jsonify({'error': 'Unsupported language'}), 400

    # Log the execution
    # Assuming you have a logging function
    # log_task_execution(user_id, language, code, result.get('output', ''), result.get('status', 'error'))

    return jsonify(result)

def init_user(username):
    from ..models.models import User
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, profile_data={})
            db.session.add(user)
            db.session.commit()
            logging.info(f"New user created: {username}")
        else:
            logging.info(f"User {username} already exists.")
        return user
    except Exception as e:
        logging.error(f"Error creating user {username}: {str(e)}")
        return None
