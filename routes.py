import logging
from flask import Blueprint, session, render_template, request, jsonify
from flask_socketio import emit
from app_extensions import socketio, db
from models import UserProfile
from utils.database import (
    add_message,
    get_conversation_history,
    get_user_profile,
    set_user_profile,
    get_existing_profiles,
    add_long_term_memory,
    add_chatroom_memory
)
from utils.intent_parser import (
    parse_intent,
    handle_write_to_file,
    handle_read_from_file,  # Re-implemented function
    handle_execute_code,     # Re-implemented function
    handle_hardware_interaction,
    handle_execute_os_command
)
from config import Config
from openai import OpenAI
import google.generativeai as genai
import os
import uuid
import json
import subprocess

main = Blueprint('main', __name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Configure Google Gemini
genai.configure(api_key=Config.GOOGLE_API_KEY)

# Define the system prompt
system_prompt = Config.SYSTEM_PROMPT

# Read the JSON Schema from the file
with open('response_schema.json', 'r') as file:
    response_format_schema = json.load(file)

# Cache for storing previously generated code and results
resource_cache = {}

WORKSPACE_DIR = "virtual_workspace"

def get_workspace_path():
    if not os.path.exists(WORKSPACE_DIR):
        os.makedirs(WORKSPACE_DIR)
    return WORKSPACE_DIR

def generate_unique_filename(extension=".py"):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    unique_id = str(uuid.uuid4())
    return f"script_{timestamp}_{unique_id}{extension}"

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/api/profiles', methods=['GET', 'POST'])
def manage_profiles():
    if request.method == 'GET':
        existing_profiles = get_existing_profiles()
        return jsonify(existing_profiles)
    elif request.method == 'POST':
        profile_data = request.json
        name = profile_data.get('name')
        set_user_profile(session.get('id'), name)
        return jsonify({"message": f"Profile {name} created."}), 201

@main.route('/api/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist("files[]")
    upload_dir = get_workspace_path()
    
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        logging.info(f"File saved at {file_path}")
    
    return jsonify({"message": "Files uploaded successfully."}), 200

@main.route('/api/message', methods=['POST'])
def handle_message():
    data = request.json
    message = data.get('message')
    intent = parse_intent(message)

    if intent == "write_to_file":
        content = data.get('content', '')
        result = handle_write_to_file(message, content)
        emit('message', {'response': result})
    
    elif intent == "read_from_file":
        result = handle_read_from_file(message)
        emit('message', {'response': result})
    
    elif intent == "execute_code":
        result = handle_execute_code(message, data.get('generated_response', ''))
        emit('message', {'response': result})
    
    elif intent == "hardware_interaction":
        result = handle_hardware_interaction(message)
        emit('message', {'response': result})
    
    elif intent == "execute_os_command":
        result = handle_execute_os_command(message)
        emit('message', {'response': result})
    
    return jsonify({"message": "Intent processed successfully."}), 200

@main.route('/api/settings', methods=['POST'])
def handle_special_message():
    data = request.json
    session_id = session.get('id')
    
    if data['type'] == 'settings':
        selected_model = data.get('model')
        selected_provider = data.get('provider')
        custom_engine = data.get('customEngine')
        config = data.get('config', {})

        logging.debug(f"Settings updated: Model={selected_model}, Provider={selected_provider}, Custom Engine={custom_engine}, Config={config}")
    
    elif data['type'] == 'profile':
        name = data.get('name')
        set_user_profile(session_id, name)
        response_message = f"Profile updated. Your name is {name}."
        add_message(session_id, session_id, 'assistant', response_message, "system")
        emit('message', {'user': "", 'assistant': response_message})
    
    return jsonify({"message": "Settings processed successfully."}), 200
