import os
import json
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_session import Session
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
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# Load local GPT-2 model
gpt2_model_path = "models/local_gpt2"
gpt2_tokenizer = GPT2Tokenizer.from_pretrained(gpt2_model_path)
gpt2_model = GPT2LMHeadModel.from_pretrained(gpt2_model_path)

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

db.init_app(app)
migrate = Migrate(app, db)

socketio = SocketIO(app)
logging.basicConfig(level=logging.DEBUG)
client = OpenAI(api_key=Config.OPENAI_API_KEY)
genai.configure(api_key=Config.GOOGLE_API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/gpt2_interact', methods=['POST'])
def gpt2_interact():
    data = request.json
    input_text = data.get("input_text", "")
    try:
        inputs = gpt2_tokenizer(input_text, return_tensors='pt')
        outputs = gpt2_model.generate(**inputs)
        decoded_output = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return jsonify({"response": decoded_output})
    except Exception as e:
        logging.error(f"Error generating GPT-2 response: {str(e)}")
        return jsonify({"error": f"Failed to generate GPT-2 response: {str(e)}"}), 500

@app.route('/api/gpt2_status', methods=['GET'])
def gpt2_status():
    try:
        inputs = gpt2_tokenizer("Test", return_tensors='pt')
        gpt2_model.generate(**inputs)
        return jsonify({'status': 'operational'})
    except Exception as e:
        logging.error(f"Error loading GPT-2 model: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

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

@app.route('/save_settings', methods=['POST'])
def save_settings():
    data = request.get_json()
    session['provider'] = data.get('provider', 'openai')  # Default to OpenAI if none provided
    session['model'] = data.get('model', 'gpt-4o')  # Default model
    session['memory_enabled'] = data.get('memory_enabled', True)  # Default to memory on
    return jsonify({'success': True})

@app.route('/get_settings', methods=['GET'])
def get_settings():
    provider = session.get('provider', 'openai')
    model = session.get('model', 'gpt-4o')
    memory_enabled = session.get('memory_enabled', True)
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
            if not model.startswith('models/') and not model.startswith('tunedModels/'):
                model = 'models/' + model

            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)

            if hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
                return {'code': response_text}
            else:
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
