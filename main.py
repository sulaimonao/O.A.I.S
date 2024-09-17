# main.py
import os
import json
import logging
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from tools.intent_parser import parse_intent_with_gpt2, handle_task
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from tools.code_execution import execute_python_code, execute_js_code, execute_bash_code
from data.memory import retrieve_memory
from models.gpt2_observer import gpt2_restructure_prompt
import google.generativeai as genai
import openai
from data.models import db, User, Session, Interaction
from tools.task_logging import log_task_execution
from datetime import datetime

# Load local GPT-2 model
gpt2_model_path = "models/local_gpt2"
gpt2_tokenizer = GPT2Tokenizer.from_pretrained(gpt2_model_path)
gpt2_model = GPT2LMHeadModel.from_pretrained(gpt2_model_path)

# Flask app setup
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)

# Initialize socket and logging
socketio = SocketIO(app)
logging.basicConfig(level=logging.DEBUG)

# Initialize OpenAI and Google Gemini
openai.api_key = Config.OPENAI_API_KEY
genai.configure(api_key=Config.GOOGLE_API_KEY)

# Routes

@app.route('/')
def home():
    return render_template('index.html')  # Main landing page

# Update routes to render 'index.html' since other templates don't exist
@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('index.html')

# API for GPT-2 Interaction
@app.route('/api/gpt2_interact', methods=['POST'])
def gpt2_interact():
    data = request.json
    input_text = data.get("input_text", "")
    try:
        session_id = session.get('session_id')
        past_interactions = retrieve_memory(session.get('user_id'), session_id)
        if not past_interactions:
            memory_prompt = input_text
        else:
            memory_prompt = f"{input_text} {past_interactions[-1].prompt}"

        inputs = gpt2_tokenizer(memory_prompt, return_tensors='pt')
        outputs = gpt2_model.generate(**inputs, max_new_tokens=100)
        decoded_output = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return jsonify({"response": decoded_output})

    except Exception as e:
        logging.error(f"Error generating GPT-2 response: {str(e)}")
        return jsonify({"error": f"Failed to generate GPT-2 response: {str(e)}"}), 500

# Check GPT-2 status
@app.route('/api/gpt2_status', methods=['GET'])
def gpt2_status():
    try:
        inputs = gpt2_tokenizer("Test", return_tensors='pt')
        gpt2_model.generate(**inputs)
        return jsonify({'status': 'operational'})
    except Exception as e:
        logging.error(f"Error loading GPT-2 model: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

# Toggle memory settings
@app.route('/toggle_memory', methods=['POST'])
def toggle_memory():
    data = request.get_json()
    memory_enabled = data.get('memory_enabled')
    if memory_enabled is not None:
        session['memory_enabled'] = memory_enabled
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid memory status'}), 400

# Get and create profiles
@app.route('/get_profiles', methods=['GET'])
def get_profiles():
    users = User.query.all()
    profile_list = [{"id": user.id, "username": user.username} for user in users]
    return jsonify(profile_list)

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
    return jsonify({'error': 'Failed to create profile. Please try again.'}), 500

# Upload File Route
@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No files selected'})
    filenames = []
    for file in files:
        if file.filename == '':
            continue
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        filenames.append(file.filename)
    if filenames:
        return jsonify({'filenames': filenames})
    else:
        return jsonify({'error': 'No files uploaded'})

# Download File Route
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory('uploads', filename, as_attachment=True)

# Delete File Route
@app.route('/delete_file/<filename>', methods=['DELETE'])
def delete_file(filename):
    filepath = os.path.join('uploads', filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'File not found'}), 404

# Get Uploaded Files
@app.route('/get_uploaded_files', methods=['GET'])
def get_uploaded_files():
    files = os.listdir('uploads')
    return jsonify(files)

# Save and retrieve settings
@app.route('/save_settings', methods=['POST'])
def save_settings():
    data = request.get_json()
    session['provider'] = data.get('provider', 'openai')
    session['model'] = data.get('model', 'gpt-4')
    session['memory_enabled'] = data.get('memory_enabled', True)
    session['temperature'] = data.get('temperature', Config.TEMPERATURE)
    session['max_tokens'] = data.get('maxTokens', Config.MAX_TOKENS)
    session['top_p'] = data.get('topP', Config.TOP_P)
    logging.debug(f"Settings saved: {session}")
    return jsonify({'success': True})

@app.route('/get_settings', methods=['GET'])
def get_settings():
    provider = session.get('provider', 'openai')
    model = session.get('model', 'gpt-4')
    memory_enabled = session.get('memory_enabled', True)
    temperature = session.get('temperature', Config.TEMPERATURE)
    max_tokens = session.get('max_tokens', Config.MAX_TOKENS)
    top_p = session.get('top_p', Config.TOP_P)
    return jsonify({
        'provider': provider,
        'model': model,
        'memory_enabled': memory_enabled,
        'temperature': temperature,
        'maxTokens': max_tokens,
        'topP': top_p
    })

# Code Execution Route
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

# Initialize user and session
def init_user(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, profile_data={})
            db.session.add(user)
            db.session.commit()
            logging.info(f"New user created: {username}")
        return user
    except Exception as e:
        logging.error(f"Error creating user {username}: {str(e)}")
        return None

def create_or_fetch_session():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User not logged in. Please create a profile."}), 401

    session_data = Session.query.filter_by(user_id=user_id, start_time=datetime.utcnow().date()).first()
    if not session_data:
        session_data = Session(user_id=user_id, topic="Default", model_used="gpt-2")
        db.session.add(session_data)
        db.session.commit()
    return session_data.id

# Generate response based on selected provider and model
def generate_llm_response(prompt, model, provider, config):
    logging.debug(f"Generating response using provider: {provider}, model: {model}")
    try:
        temperature = config.get('temperature', Config.TEMPERATURE)
        max_tokens = config.get('maxTokens', Config.MAX_TOKENS)
        top_p = config.get('topP', Config.TOP_P)

        if provider == 'openai':
            # OpenAI API call
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": Config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True
            )
            content = ""
            for chunk in response:
                if 'choices' in chunk and chunk.choices:
                    delta_content = chunk.choices[0].delta.get('content', '')
                    if delta_content:
                        content += delta_content
                        emit('message', {'assistant': delta_content})
            return {'code': content}

        elif provider == 'google':
            # Google API call
            genai_model = genai.GenerativeModel('models/' + model)
            response = genai_model.generate_content(prompt)

            if hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
                return {'code': response_text}
            else:
                return {'error': 'No valid response from Google API'}

        elif provider == 'local':
            # Local GPT-2 inference
            inputs = gpt2_tokenizer(prompt, return_tensors='pt')
            outputs = gpt2_model.generate(**inputs, max_new_tokens=100)
            decoded_output = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
            return {'code': decoded_output}

    except Exception as e:
        logging.error(f"Error generating response with {provider} and {model}: {str(e)}")
        return {'error': f"Error generating response with {provider} and {model}: {str(e)}"}

# Socket.IO message handling
@socketio.on('message')
def handle_message(data):
    logging.debug(f"Received data: {data}")
    data = json.loads(data)
    message = data['message']
    model = data.get('model') or session.get('model', Config.OPENAI_MODEL)
    provider = data.get('provider') or session.get('provider', 'openai')
    config = data.get('config', {})  # Default to empty config if not provided
    user_id = session.get('user_id', 'anonymous')

    intent = parse_intent_with_gpt2(message)

    if intent in ["create_folder", "delete_file", "create_file", "delete_folder", "execute_python_code", "execute_bash_code", "execute_js_code"]:
        result = handle_task(intent, message)
        emit('message', {'response': result})
        emit('message', {'feedback_prompt': "Was the task executed correctly? (yes/no)"})

        if session.get('memory_enabled', True):
            session_id = create_or_fetch_session()
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
                # Emit assistant message only if not already streamed
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

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, debug=True)
