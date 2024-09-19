import os
import json
import logging
import subprocess
import sys
import io
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from data.models import db, User, Session as UserSession, Interaction, CodeExecutionLog
from data.memory import retrieve_memory
from tools.code_execution import execute_python_code, execute_js_code, execute_bash_code
from tools.task_logging import log_task_execution
from tools.intent_parser import parse_intent_with_gpt2, handle_task
from tools.file_operations import read_file, write_file
from config import Config
from datetime import datetime
from openai import OpenAI  # Example, replace with actual import if different
import google.generativeai as genai

# Initialize Flask app and configurations
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
db.init_app(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)
logging.basicConfig(level=logging.DEBUG)

# Initialize GPT-2 model
gpt2_model_path = "models/local_gpt2"
gpt2_tokenizer = GPT2Tokenizer.from_pretrained(gpt2_model_path)
gpt2_model = GPT2LMHeadModel.from_pretrained(gpt2_model_path)

# Initialize OpenAI and Google API clients
client = OpenAI(api_key=Config.OPENAI_API_KEY)
genai.configure(api_key=Config.GOOGLE_API_KEY)

# Placeholder WordLlama status check (replace with actual implementation)
def get_wordllama_status():
    return {'status': 'operational', 'current_task': 'Idle'}

# Routes for main pages
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('index.html')

# API for GPT-2 interaction
@app.route('/api/gpt2_interact', methods=['POST'])
def gpt2_interact():
    data = request.json
    input_text = data.get("input_text", "")
    if not input_text:
        return jsonify({"error": "No input text provided"}), 400

    try:
        session_id = session.get('session_id')
        past_interactions = retrieve_memory(session.get('user_id'), session_id)
        memory_prompt = input_text if not past_interactions else f"{input_text} {past_interactions[-1].prompt}"
        inputs = gpt2_tokenizer(memory_prompt, return_tensors='pt')
        outputs = gpt2_model.generate(**inputs, max_new_tokens=100)
        decoded_output = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return jsonify({"response": decoded_output})
    except Exception as e:
        logging.error(f"Error generating GPT-2 response: {str(e)}")
        return jsonify({"error": f"Failed to generate GPT-2 response: {str(e)}"}), 500

# API for GPT-2 status check
@app.route('/api/gpt2_status', methods=['GET'])
def gpt2_status():
    try:
        inputs = gpt2_tokenizer("Test", return_tensors='pt')
        gpt2_model.generate(**inputs)
        return jsonify({'status': 'operational'})
    except Exception as e:
        logging.error(f"Error loading GPT-2 model: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

# Toggle memory setting
@app.route('/toggle_memory', methods=['POST'])
def toggle_memory():
    data = request.get_json()
    memory_enabled = data.get('memory_enabled')
    if memory_enabled is not None:
        session['memory_enabled'] = memory_enabled
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid memory status'}), 400

profile_cache = {}

# Get profiles API
@app.route('/get_profiles', methods=['GET'])
def get_profiles():
    if 'profiles' in profile_cache:
        return jsonify(profile_cache['profiles'])

    users = User.query.all()
    profile_list = [{"id": user.id, "username": user.username} for user in users]
    profile_cache['profiles'] = profile_list
    return jsonify(profile_list)

# Create profile API
@app.route('/create_profile', methods=['POST'])
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

# File upload API
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        return jsonify({'filename': file.filename})

# Save settings API
@app.route('/save_settings', methods=['POST'])
def save_settings():
    data = request.get_json()
    session['provider'] = data.get('provider', 'openai')
    session['model'] = data.get('model', 'gpt-4o')
    session['memory_enabled'] = data.get('memory_enabled', True)
    logging.debug(f"Settings saved: {session}")
    return jsonify({'success': True})

# Get settings API
@app.route('/get_settings', methods=['GET'])
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

# Generate GPT-2 response with max token limit
@app.route('/generate_gpt2', methods=['POST'])
def generate_gpt2():
    data = request.get_json()
    prompt = data.get('prompt', '')
    max_tokens = data.get('max_tokens', 100)

    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    inputs = gpt2_tokenizer.encode(prompt, return_tensors="pt")
    outputs = gpt2_model.generate(inputs, max_length=max_tokens)
    response = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
    return jsonify({'response': response})

# Code execution API
@app.route('/execute_code', methods=['POST'])
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

    log_task_execution(user_id, language, code, result.get('output', ''), result.get('status', 'error'))
    return jsonify(result)

# Initialize user or fetch existing one
def init_user(username):
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

# Create or fetch session data
def create_or_fetch_session():
    user_id = session.get('user_id')
    if not user_id:
        logging.error("User ID not found in session.")
        return jsonify({"error": "User not logged in. Please create a profile."}), 401

    session_data = UserSession.query.filter_by(user_id=user_id, start_time=datetime.utcnow().date()).first()
    if not session_data:
        session_data = UserSession(user_id=user_id, topic="Default", model_used="gpt-2")
        db.session.add(session_data)
        db.session.commit()
    return session_data.id

# Generate LLM response based on provider and model
def generate_llm_response(prompt, model, provider, config):
    try:
        temperature = config.get('temperature', Config.TEMPERATURE)
        max_tokens = config.get('maxTokens', Config.MAX_TOKENS)
        top_p = config.get('topP', Config.TOP_P)

        if provider == 'openai':
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True
            )

            content = ""
            for chunk in stream:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta_content = chunk.choices[0].delta.content
                    if delta_content:
                        content += delta_content
                        emit('message', {'assistant': delta_content})
            return {'code': content}

        elif provider == 'google':
            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)

            if hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
                return {'code': response_text}
            else:
                return {'error': 'No valid response from Google API'}

        elif provider in ['local', 'gpt-2-local']:
            inputs = gpt2_tokenizer(prompt, return_tensors='pt')
            max_new_tokens = config.get('max_new_tokens', 100)
            outputs = gpt2_model.generate(**inputs, max_new_tokens=max_new_tokens)
            decoded_output = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
            return {'code': decoded_output}

    except Exception as e:
        logging.error(f"Error generating response with provider {provider} and model {model}: {str(e)}")
        return {'error': f"Error generating response with {provider} and {model}: {str(e)}"}

# Handle incoming socket message and parse intent
@socketio.on('message')
def handle_message(data):
    logging.debug(f"Received data: {data}")
    data = json.loads(data)
    message = data['message']
    model = data.get('model') or session.get('model', Config.OPENAI_MODEL)
    provider = data.get('provider') or session.get('provider', 'openai')
    config = data.get('config', {})

    intent = parse_intent_with_gpt2(message)

    if intent in ["create_folder", "delete_file", "create_file", "delete_folder", "execute_python_code", "execute_bash_code", "execute_js_code"]:
        result = handle_task(intent, message)
        emit('message', {'response': result})
        emit('message', {'feedback_prompt': "Was the task executed correctly? (yes/no)"})

        if session.get('memory_enabled', True):
            session_id = create_or_fetch_session(user_id)
            past_memory = retrieve_memory(user_id, session_id, task_type=intent)
            if past_memory:
                emit('message', {'memory': past_memory})
            interaction = Interaction(
                session_id=session_id,
                prompt=message,
                response=result,
                task_outcome="success" if result != "Unknown intent." else "failure"
            )
            db.session.add(interaction)
            db.session.commit()

    elif intent == "feedback":
        user_feedback = message.lower()
        last_interaction = Interaction.query.order_by(Interaction.timestamp.desc()).first()
        if last_interaction:
            last_interaction.feedback = user_feedback
            db.session.commit()
            emit('message', {'response': "Thank you for the feedback!"})

    else:
        code_response = generate_llm_response(message, model, provider, config)
        if 'code' in code_response:
            if provider != 'openai':
                emit('message', {'assistant': code_response['code']})
        else:
            emit('message', {'error': code_response['error']})

    if intent == "retrieve_memory":
        memory = retrieve_memory(user_id)
        emit('message', {'memory': memory})

    if intent == "system_health_check":
        health_data = system_health_check()
        emit('message', {'response': health_data})

    elif intent == "map_file_system":
        file_map = map_file_system()
        emit('message', {'response': file_map})

# Update models status via socket.io
@socketio.on('status_update')
def handle_status_update():
    try:
        # Check GPT-2 status
        gpt2_status = gpt2_model.generate(gpt2_tokenizer.encode("status check", return_tensors='pt'))
        gpt2_status_text = "Operational" if gpt2_status else "Error"
        
        # Get WordLlama status
        wordllama_status = get_wordllama_status()

        emit('status_update', {
            'gpt2': {
                'status': gpt2_status_text,
                'current_task': 'Idle'
            },
            'wordllama': wordllama_status
        })
    except Exception as e:
        logging.error(f"Error during status update: {str(e)}")

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, debug=True)
