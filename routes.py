import logging
from flask import Blueprint, session, render_template, request, jsonify
from flask_socketio import emit
from app_extensions import socketio, db
from models import UserProfile
from utils.database import add_message, get_conversation_history, get_user_profile, set_user_profile, get_existing_profiles, add_long_term_memory, add_chatroom_memory
from utils.intent_parser import (
    parse_intent,
    handle_write_to_file,
    handle_read_from_file,
    handle_execute_code,
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
        if not memory_setting['enabled']:
            return jsonify({'error': 'Memory must be enabled to create a profile.'}), 400
        data = request.get_json()
        profile_name = data.get('name')
        database_name = f"{profile_name}_database.db"
        if profile_name and not UserProfile.query.filter_by(name=profile_name).first():
            new_profile = UserProfile(session_id=str(uuid.uuid4()), name=profile_name, database_name=database_name)
            db.session.add(new_profile)
            db.session.commit()
            return jsonify({'name': profile_name}), 201
        else:
            return jsonify({'error': 'Profile already exists or invalid name'}), 400

@main.route('/api/profiles/select', methods=['POST'])
def select_profile():
    data = request.get_json()
    profile_name = data.get('name')
    logging.debug(f"Selecting profile: {profile_name}")
    profile = UserProfile.query.filter_by(name=profile_name).first()
    logging.debug(f"Profile found: {profile}")
    if profile:
        session['user_profile'] = {'name': profile_name, 'database_name': profile.database_name}
        return jsonify({'selected': profile_name}), 200
    else:
        return jsonify({'error': 'Profile not found'}), 404


@main.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify(error="No files part"), 400

    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    # Create a unique directory for the session
    upload_dir = os.path.join('uploads', str(uuid.uuid4()))
    os.makedirs(upload_dir, exist_ok=True)

    filenames = []
    for file in files:
        if file:
            file_path = os.path.join(upload_dir, file.filename)
            file.save(file_path)
            filenames.append(file.filename)

    return jsonify(filenames=filenames, folder=upload_dir)

@socketio.on('message')
def handle_message(data):
    logging.debug(f"Received message: {data}")

    session_id = session.get('id')
    if not session_id:
        emit('message', {'error': 'Session ID is missing.'})
        return

    user_id = session_id
    data = data if isinstance(data, dict) else json.loads(data)
    message = data.get('message')

    # Direct communication with the LLM to generate content or code
    generated_response = communicate_with_llm(message, data['model'], data['provider'], data['config'])

    # Check if the response should be executed as code or saved to a file
    if "execute this code" in message.lower() or "generate and execute" in message.lower():
        result = handle_execute_code(message, generated_response)
    elif "save this to a file" in message.lower():
        result = handle_write_to_file(message, generated_response)
    else:
        result = generated_response

    # Add the message and result to the chat history
    add_message(session_id, user_id, 'user', message, data['model'])
    add_message(session_id, user_id, 'assistant', result, data['model'])

    # Emit the response back to the user
    emit('message', {'user': message, 'assistant': result})

def communicate_with_llm(message, model, provider, config):
    # Communicate with the LLM and get the response
    try:
        if provider == 'openai':
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                temperature=float(config['temperature']),
                max_tokens=int(config['maxTokens']),
                top_p=float(config['topP']),
                frequency_penalty=0,
                presence_penalty=0
            )

            logging.debug(f"OpenAI response object: {response}")
            return response.choices[0].message.content

        elif provider == 'google':
            logging.debug("Processing message with Google Gemini")

            chat_session = genai.GenerativeModel(
                model_name=model,
                generation_config={
                    "temperature": float(config['temperature']),
                    "top_p": float(config['topP']),
                    "max_output_tokens": int(config['maxTokens'])
                },
                system_instruction="You are an assistant"
            ).start_chat(
                history=[
                    {"role": "user", "parts": [message]}
                ]
            )

            response = chat_session.send_message(message)

            logging.debug(f"Google response object: {response}")

            try:
                response_content = ''.join([part.text for part in response.candidates[0].content.parts])
            except AttributeError as e:
                logging.error(f"Error extracting text from Google response parts: {e}, raw response: {response}")
                return "Unexpected response format from Google Gemini."

            return response_content

        else:
            return "Provider not supported."

    except Exception as e:
        logging.error(f"Error communicating with LLM: {e}")
        return f"Failed to communicate with the LLM provider: {e}"

memory_setting = {'enabled': True}

@main.route('/api/memory', methods=['GET', 'POST'])
def manage_memory():
    if request.method == 'GET':
        return jsonify(memory_setting)
    elif request.method == 'POST':
        data = request.get_json()
        enabled = data.get('enabled')
        memory_setting['enabled'] = enabled
        return jsonify(memory_setting), 200

def handle_special_message(data):
    session_id = session.get('id')
    user_id = session_id

    if data['type'] == 'settings':
        selected_model = data.get('model')
        selected_provider = data.get('provider')
        custom_engine = data.get('customEngine')
        config = data.get('config', {})

        logging.debug(f"Settings updated: Model={selected_model}, Provider={selected_provider}, Custom Engine={custom_engine}, Config={config}")

    elif data['type'] == 'profile':
        name = data.get('name')
        active = data.get('active')

        if active and name:
            set_user_profile(session_id, name)
            response_message = f"Profile updated. Your name is {name}."
        else:
            response_message = "Profile deactivated."

        add_message(session_id, user_id, 'assistant', response_message, "system")
        emit('message', {'user': "", 'assistant': response_message})

    elif data['type'] == 'memory':
        long_term_memory = data.get('longTermMemory')
        chatroom_memory = data.get('chatroomMemory')

        if long_term_memory:
            response_message = "Long-term memory is now active."
            add_long_term_memory(session_id, response_message)
        else:
            response_message is "Long-term memory is now inactive."

        add_message(session_id, user_id, 'assistant', response_message, "system")
        emit('message', {'user': "", 'assistant': response_message})

        if chatroom_memory:
            response_message = "Chatroom memory is now active."
            add_chatroom_memory(session_id, response_message)
        else:
            response_message is "Chatroom memory is now inactive."

        add_message(session_id, user_id, 'assistant', response_message, "system")
        emit('message', {'user': "", 'assistant': response_message})
