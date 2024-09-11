import os
import json
import logging
from flask import Flask, render_template, request, jsonify, session  # Added session
from flask_socketio import SocketIO, emit
from openai import OpenAI
import google.generativeai as genai
from config import Config
from tools.intent_parser import parse_intent_with_gpt2, handle_task
from models.gpt2_observer import gpt2_restructure_prompt
from tools.file_operations import read_file, write_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from data.models import db, User, Session, Interaction
from data.memory import retrieve_memory
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')  # Required for session handling

# Initialize the database with Flask
db.init_app(app)

# Add Flask-Migrate
migrate = Migrate(app, db)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

socketio = SocketIO(app)

logging.basicConfig(level=logging.DEBUG)

# Configure OpenAI GPT
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Configure Google Gemini
genai.configure(api_key=Config.GOOGLE_API_KEY)

def init_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, profile_data={})
        db.session.add(user)
        db.session.commit()
    return user

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/toggle_memory', methods=['POST'])
def toggle_memory():
    data = request.get_json()
    memory_enabled = data.get('memory_enabled')
    if memory_enabled is not None:
        # Save memory status in session
        session['memory_enabled'] = memory_enabled
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid memory status'}), 400

@app.route('/get_profiles', methods=['GET'])
def get_profiles():
    """Fetch all user profiles from the database."""
    users = User.query.all()
    profile_list = [{"id": user.id, "username": user.username} for user in users]
    return jsonify(profile_list)

@app.route('/create_profile', methods=['POST'])
def create_profile():
    data = request.get_json()
    username = data.get('username')
    if username:
        user = init_user(username)
        return jsonify({'success': True})
    return jsonify({'error': 'Invalid username'}), 400

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

def create_or_fetch_session(user_id):
    session = Session.query.filter_by(user_id=user_id, start_time=datetime.utcnow().date()).first()
    if not session:
        session = Session(user_id=user_id, topic="Default", model_used="gpt-2")
        db.session.add(session)
        db.session.commit()
    return session.id

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
                        logging.debug(f'Streaming response chunk: {delta_content}')
            return {'code': content}

        elif provider == 'google':
            # Ensure that model starts with the correct path format
            if not model.startswith('models/') and not model.startswith('tunedModels/'):
                model = 'models/' + model

            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)

            # Log the response for debugging
            logging.debug(f"Google API Response: {response}")

            if hasattr(response, 'candidates') and response.candidates:
                # Return the response content properly
                response_text = response.candidates[0].content.parts[0].text
                return {'code': response_text}
            else:
                logging.error("No candidates returned in Google API response.")
                return {'error': 'No valid response from Google API'}

    except Exception as e:
        logging.error(f"Error generating response for provider {provider} and model {model}: {str(e)}")
        return {'error': f"Error with {provider} provider and {model} model: {str(e)}"}

@socketio.on('message')
def handle_message(data):
    data = json.loads(data)
    message = data['message']
    model = data.get('model') or Config.OPENAI_MODEL
    provider = data['provider']
    config = data.get('config', {})

    intent = parse_intent_with_gpt2(message)

    if intent in ["create_folder", "delete_file", "create_file", "delete_folder", "execute_python_code", "execute_bash_code", "execute_js_code"]:
        result = handle_task(intent, message)
        emit('message', {'response': result})

        emit('message', {'feedback_prompt': "Was the task executed correctly? (yes/no)"})
        
        if session.get('memory_enabled', True):  # Default to True
            session_id = create_or_fetch_session(user_id)  # Placeholder function
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
            emit('message', {'user': message, 'assistant': code_response['code']})
        else:
            emit('message', {'user': message, 'error': code_response['error']})

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
