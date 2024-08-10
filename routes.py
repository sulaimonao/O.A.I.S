# routes.py
import logging
from flask import Blueprint, session, render_template, request, jsonify
from flask_socketio import emit
from app_extensions import socketio, db
from models import UserProfile
from utils.database import add_message, get_conversation_history, get_user_profile, set_user_profile, get_existing_profiles, add_long_term_memory, add_chatroom_memory
from utils.validation import validate_response
from config import Config
from openai import OpenAI
import google.generativeai as genai
import os
import uuid
import json

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
    model = data.get('model') or Config.OPENAI_MODEL
    provider = data.get('provider')

    try:
        if provider == 'openai':
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                top_p=Config.TOP_P,
                frequency_penalty=0,
                presence_penalty=0
            )

            logging.debug(f"OpenAI response object: {response}")

            response_content = response.choices[0].message.content
            response_data = {
                "role": "assistant",
                "content": response_content
            }

        elif provider == 'google':
            logging.debug("Processing message with Google Gemini")

            # Create a chat session with Google Gemini
            chat_session = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 8192
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
                emit('message', {'error': 'Unexpected response format from Google Gemini.'})
                return

            response_data = {
                "role": "assistant",
                "content": response_content
            }

        logging.debug(f"Response data: {response_data}")

        if validate_response(response_data, provider):
            model_name = model if isinstance(model, str) else model.model_name
            add_message(session_id, user_id, 'assistant', response_data["content"], model_name)
            emit('message', {'user': message, 'assistant': response_data["content"]})
        else:
            emit('message', {'error': 'Invalid response format.'})
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        emit('message', {'error': str(e)})

memory_setting = {'enabled': False}

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
            response_message = "Long-term memory is now inactive."

        add_message(session_id, user_id, 'assistant', response_message, "system")
        emit('message', {'user': "", 'assistant': response_message})

        if chatroom_memory:
            response_message = "Chatroom memory is now active."
            add_chatroom_memory(session_id, response_message)
        else:
            response_message = "Chatroom memory is now inactive."

        add_message(session_id, user_id, 'assistant', response_message, "system")
        emit('message', {'user': "", 'assistant': response_message})
