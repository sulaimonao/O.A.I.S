import json
import logging
from flask import Blueprint, session, render_template, request, jsonify
from flask_socketio import emit
from app_extensions import socketio, db
from models import UserProfile
from utils.database import add_message, add_long_term_memory, add_chatroom_memory, get_conversation_history, get_user_profile, set_user_profile, create_db, get_existing_profiles, check_and_create_tables
from utils.file_operations import write_file
from utils.intent_parser import parse_intent, handle_write_to_file, handle_execute_code
from utils.code_execution import execute_code
from config import Config
from openai import OpenAI
import google.generativeai as genai
import uuid
import os

from utils.llm import generate_code_via_llm

# Initialize OpenAI client
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Configure Google Gemini
genai.configure(api_key=Config.GOOGLE_API_KEY)

# Cache for storing previously generated code and results
resource_cache = {}

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

memory_setting = {'enabled': False}

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
            if not os.path.exists(database_name):
                create_db(database_name)
                check_and_create_tables(database_name)
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

@main.route('/api/memory', methods=['GET', 'POST'])
def manage_memory():
    if request.method == 'GET':
        return jsonify(memory_setting)
    elif request.method == 'POST':
        data = request.get_json()
        enabled = data.get('enabled')
        memory_setting['enabled'] = enabled
        return jsonify(memory_setting), 200

@socketio.on('message')
def handle_message(data):
    logging.debug(f"Received message: {data}")
    
    session_id = session.get('id')
    if not session_id:
        emit('message', {'error': 'Session ID is missing.'})
        return

    user_id = session_id  # This could be enhanced to use actual user IDs in a real system

    if 'user_profile' not in session:
        session['user_profile'] = {'name': None, 'awaiting_confirmation': False}

    data = json.loads(data)
    if 'type' in data:
        handle_special_message(data)
        return

    message = data['message']
    model = data.get('model') or (Config.GOOGLE_MODEL if data['provider'] == 'google' else Config.OPENAI_MODEL)
    provider = data['provider']
    filename = data.get('filename')
    custom_engine = data.get('customEngine')
    config = data.get('config', {})

    if custom_engine:
        model = custom_engine

    if provider == 'google' and model in ['gpt-4', 'gpt-4-mini']:
        emit('message', {'error': 'Invalid model for the selected provider.'})
        return

    if provider == 'openai' and model in ['gemini-1.5-pro', 'gemini-1.5-flash']:
        emit('message', {'error': 'Invalid model for the selected provider.'})
        return

    logging.debug(f"Message: {message}, Model: {model}, Provider: {provider}, Filename: {filename}, Config: {config}")

    database_path = Config.DATABASE
    if memory_setting['enabled'] and 'user_profile' in session:
        database_path = session['user_profile']['database_name']

    add_message(session_id, user_id, 'user', message, model, database_path)

    # Handle user introduction and confirmation
    if session['user_profile']['awaiting_confirmation']:
        if message.lower() in ['yes', 'y']:
            session['user_profile']['awaiting_confirmation'] = False
            set_user_profile(session_id, session['user_profile']['name'], database_path)
            response_message = f"Great! I will remember your name, {session['user_profile']['name']}."
            add_message(session_id, user_id, 'assistant', response_message, model, database_path)
            emit('message', {'user': message, 'assistant': response_message})
        else:
            session['user_profile']['name'] = None
            session['user_profile']['awaiting_confirmation'] = False
            response_message = "Okay, I won't remember your name."
            add_message(session_id, user_id, 'assistant', response_message, model, database_path)
            emit('message', {'user': message, 'assistant': response_message})
        return

    if "my name is" in message.lower():
        parts = message.lower().split("my name is", 1)
        if len(parts) > 1 and parts[1].strip():
            name = parts[1].strip().split(' ')[0]
            session['user_profile']['name'] = name
            session['user_profile']['awaiting_confirmation'] = True
            response_message = f"Did I get that right? Is your name {name}? Please reply with 'yes' or 'no'."
            add_message(session_id, user_id, 'assistant', response_message, model, database_path)
            emit('message', {'user': message, 'assistant': response_message})
        else:
            response_message = "I didn't catch your name. Please tell me again by saying 'My name is [Your Name]'."
            add_message(session_id, user_id, 'assistant', response_message, model, database_path)
            emit('message', {'user': message, 'assistant': response_message})
        return

    if "what is my name" in message.lower() or "do you remember me" in message.lower():
        name = session['user_profile']['name']
        if not name:
            profile = get_user_profile(session_id, database_path)
            if profile:
                name = profile[0]
                session['user_profile']['name'] = name

        if name:
            response_message = f"Your name is {name}."
        else:
            response_message = "I don't know your name. Please tell me your name by saying 'My name is [Your Name]'."
        add_message(session_id, user_id, 'assistant', response_message, model, database_path)
        emit('message', {'user': message, 'assistant': response_message})
        return

    intent = parse_intent(message)
    
    if intent == "write_to_file":
        content_response = generate_code_via_llm(message, model, provider, config)
        if 'code' in content_response:
            content = content_response['code']
            result = handle_write_to_file(message, content)
            add_message(session_id, user_id, 'assistant', result, model, database_path)
            emit('message', {'user': message, 'result': result})
            logging.debug(f"Emitting write_to_file result: {result}")
        else:
            emit('message', {'user': message, 'error': content_response['error']})
            logging.error(f'Error generating content: {content_response["error"]}')
    elif intent == "execute_code":
        code_response = generate_code_via_llm(message, model, provider, config)
        if 'code' in code_response:
            result = handle_execute_code(message, code_response['code'], session_id)
            add_message(session_id, user_id, 'assistant', result, model, database_path)
            emit('message', {'user': message, 'result': result})
            logging.debug(f"Emitting execute_code result: {result}")
        else:
            emit('message', {'user': message, 'error': code_response['error']})
            logging.error(f'Error generating code: {code_response["error"]}')
    elif "generate code" in message.lower():
        code_response = generate_code_via_llm(message, model, provider, config)
        if 'code' in code_response:
            result = execute_code(code_response['code'])
            write_file('output.txt', result)
            add_message(session_id, user_id, 'assistant', result, model, database_path)
            emit('message', {'user': message, 'code': code_response['code'], 'result': result})
            logging.debug(f'Emitting code response: {code_response["code"]}')
        else:
            emit('message', {'user': message, 'error': code_response['error']})
            logging.error(f'Error emitting code response: {code_response["error"]}')
    else:
        history = get_conversation_history(session_id, database_path)
        history.append({"role": "system", "content": Config.SYSTEM_PROMPT})
        history.append({"role": "user", "content": message})
        try:
            if provider == 'openai':
                response = openai_client.Chat.completions.create(
                    model=model,
                    messages=history,
                    max_tokens=config.get('maxTokens', Config.MAX_TOKENS),
                    temperature=config.get('temperature', Config.TEMPERATURE),
                    top_p=config.get('topP', Config.TOP_P)
                )
                content = response['choices'][0]['message']['content']
            elif provider == 'google':
                genai_model = genai.GenerativeModel(model)
                if filename:
                    filepath = os.path.join('uploads', filename)
                    file = genai.upload_file(filepath)
                    response = genai_model.generate_content([message, file])
                else:
                    response = genai_model.generate_content(message)
                content = response.text

            add_message(session_id, user_id, 'assistant', content, model, database_path)
            logging.debug(f'{provider.capitalize()} Response: {content}')
            emit('message', {'user': message, 'assistant': content})
        except Exception as e:
            logging.error(f'Error with {provider.capitalize()}: {str(e)}')
            emit('message', {'error': str(e)})

def handle_special_message(data):
    session_id = session.get('id')
    user_id = session_id  # This could be enhanced to use actual user IDs in a real system

    if data['type'] == 'settings':
        selected_model = data.get('model')
        selected_provider = data.get('provider')
        custom_engine = data.get('customEngine')
        config = data.get('config', {})

        # Process settings data
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
