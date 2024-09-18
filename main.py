import os
import json
import logging
from flask import Flask, render_template, request, jsonify, session as flask_session, send_from_directory
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session as FlaskSession
from flask_migrate import Migrate
from openai import OpenAI
import google.generativeai as genai
from config import Config
from tools.intent_parser import parse_intent_with_gpt2, handle_task
from models.gpt2_observer import gpt2_restructure_prompt
from tools.file_operations import read_file, write_file
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from tools.code_execution import execute_python_code, execute_js_code, execute_bash_code
from data.models import db, User, Session, Interaction
from data.memory import retrieve_memory
from datetime import datetime

# Flask app initialization
app = Flask(__name__)
app.config.from_object(Config)

# Setting the session type in the configuration
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize Flask-Session
sess = FlaskSession()  # Renaming to avoid conflict
sess.init_app(app)

# Other initializations
socketio = SocketIO(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Integrating database migration

# Setting up GPT-2 tokenizer and model
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')

# Routes and Task Handlers
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/intent', methods=['POST'])
def handle_intent():
    data = request.json
    intent = data.get('intent')
    response = handle_task(intent)
    return jsonify({'response': response})

@app.route('/code_execution', methods=['POST'])
def execute_code():
    data = request.json
    code_type = data.get('code_type')
    code = data.get('code')
    if code_type == 'python':
        result = execute_python_code(code)
    elif code_type == 'javascript':
        result = execute_js_code(code)
    elif code_type == 'bash':
        result = execute_bash_code(code)
    else:
        result = "Unsupported code type."
    return jsonify({'result': result})

# GPT-2 based intent handler
@app.route('/gpt2_intent', methods=['POST'])
def gpt2_intent():
    data = request.json
    prompt = data.get('prompt')
    structured_prompt = gpt2_restructure_prompt(prompt)
    response = parse_intent_with_gpt2(structured_prompt)
    return jsonify({'response': response})

# Memory retrieval and profile management
@app.route('/toggle_memory', methods=['POST'])
def toggle_memory():
    data = request.get_json()
    memory_enabled = data.get('memory_enabled')
    if memory_enabled is not None:
        session['memory_enabled'] = memory_enabled
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid memory status'}), 400

@app.route('/get_profiles', methods=['GET'])
def get_profiles():
    users = User.query.all()
    profile_list = [{"id": user.id, "username": user.username} for user in users]
    return jsonify(profile_list)

@app.route('/create_profile', methods=['POST'])
def create_profile():
    data = request.get_json()
    username = data.get('username')
    if username:
        user = init_user(username)
        return jsonify({'success': True, 'id': user.id})
    return jsonify({'error': 'Invalid username'}), 400

@app.route('/save_settings', methods=['POST'])
def save_settings():
    data = request.get_json()
    session['provider'] = data.get('provider', 'openai')
    session['model'] = data.get('model', 'gpt-4o')
    session['memory_enabled'] = data.get('memory_enabled', True)
    logging.debug(f"Settings saved: {session}")
    return jsonify({'success': True})

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

def init_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, profile_data={})
        db.session.add(user)
        db.session.commit()
    return user

def create_or_fetch_session(user_id):
    user_id = session.get('user_id')
    if not user_id:
        logging.error("User ID not found in session.")
        emit('message', {'error': 'User not logged in.'})
        return
    session = Session.query.filter_by(user_id=user_id, start_time=datetime.utcnow().date()).first()
    if not session:
        session = Session(user_id=user_id, topic="Default", model_used="gpt-2")
        db.session.add(session)
        db.session.commit()
    return session.id

def generate_llm_response(prompt, model, provider, config):
    logging.debug(f"Generating response using provider: {provider}, model: {model}")
    try:
        temperature = config.get('temperature', Config.TEMPERATURE)
        max_tokens = config.get('maxTokens', Config.MAX_TOKENS)
        top_p = config.get('topP', Config.TOP_P)

        if provider == 'openai':
            logging.debug('Using OpenAI model')
            stream = OpenAI(api_key=Config.OPENAI_API_KEY).chat.completions.create(
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
                        logging.debug(f'Streaming response chunk: {delta_content}')
            return {'code': content}

        elif provider == 'google':
            logging.debug('Using Google model')
            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)

            if hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
                return {'code': response_text}
            else:
                return {'error': 'No valid response from Google API'}

        elif provider in ['local', 'gpt-2-local']:
            logging.debug('Using Local GPT-2 model')
            inputs = tokenizer(prompt, return_tensors='pt')
            outputs = model.generate(**inputs, max_new_tokens=100)
            decoded_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return {'code': decoded_output}

    except Exception as e:
        logging.error(f"Error generating response with provider {provider} and model {model}: {str(e)}")
        return {'error': f"Error generating response with {provider} and {model}: {str(e)}"}

@socketio.on('message')
def handle_message(data):
    logging.debug(f"Received data: {data}")
    data = json.loads(data)
    message = data['message']
    model = data.get('model') or session.get('model', Config.OPENAI_MODEL)
    provider = data.get('provider') or session.get('provider', 'openai')
    config = data.get('config', {})  # Default to empty config if not provided

    intent = parse_intent_with_gpt2(message)

    if intent in ["create_folder", "delete_file", "create_file", "delete_folder", "execute_python_code", "execute_bash_code", "execute_js_code"]:
        result = handle_task(intent, message)
        emit('message', {'response': result})
        emit('message', {'feedback_prompt': "Was the task executed correctly? (yes/no)"})

        if session.get('memory_enabled', True):
            session_id = create_or_fetch_session(user_id)
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
            emit('message', {'assistant': code_response['code']})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, debug=True)