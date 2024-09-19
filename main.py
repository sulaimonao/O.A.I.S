import os
import json
import logging
import subprocess
import sys
import io
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_session import Session
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from data.models import db, User, Session, Interaction
from data.memory import retrieve_memory
from tools.code_execution import execute_python_code, execute_js_code, execute_bash_code
from tools.task_logging import log_task_execution
from tools.intent_parser import parse_intent_with_gpt2, handle_task
from config import Config  # Import Config class from config.py
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)  # Use the imported Config class
app.secret_key = Config.SECRET_KEY

db.init_app(app)
socketio = SocketIO(app)
logging.basicConfig(level=logging.DEBUG)

# Initialize GPT-2 model
gpt2_model_path = "models/local_gpt2"
gpt2_tokenizer = GPT2Tokenizer.from_pretrained(gpt2_model_path)
gpt2_model = GPT2LMHeadModel.from_pretrained(gpt2_model_path)

# Routes updated to ensure proper template rendering
@app.route('/')
def home():
    return render_template('index.html')  # Rendering the correct template

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('index.html')

# Updated API route to handle missing input gracefully
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

profile_cache = {}

@app.route('/get_profiles', methods=['GET'])
def get_profiles():
    if 'profiles' in profile_cache:
        return jsonify(profile_cache['profiles'])

    users = User.query.all()
    profile_list = [{"id": user.id, "username": user.username} for user in users]
    profile_cache['profiles'] = profile_list
    return jsonify(profile_list)

@app.route('/create_profile', methods=['POST'])
def create_profile():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Invalid username'}), 400  # Handle missing username

    user = init_user(username)
    if user:
        session['user_id'] = user.id  # Store user ID in session
        return jsonify({'success': True, 'id': user.id})
    else:
        return jsonify({'error': 'Failed to create user profile. Please try again.'}), 500  # Handle user creation failure

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

@app.route('/generate_gpt2', methods=['POST'])
def generate_gpt2():
    data = request.get_json()
    prompt = data.get('prompt', '')
    max_tokens = data.get('max_tokens', 100)  # Default value is 100
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    # Generate response from GPT-2 with customizable token limit
    inputs = gpt2_tokenizer.encode(prompt, return_tensors="pt")
    outputs = gpt2_model.generate(inputs, max_length=max_tokens)  # Customizable max tokens
    response = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return jsonify({'response': response})

@app.route('/execute_code', methods=['POST'])
def execute_code_route():
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'python')  # Default to Python

    if not code:
        return jsonify({'error': 'No code provided'}), 400

    user_id = session.get('user_id', 'anonymous')  # Get user ID or 'anonymous'

    # Execute the code based on the language
    if language == 'python':
        result = execute_python_code(code)
    elif language == 'javascript':
        result = execute_js_code(code)
    elif language == 'bash':
        result = execute_bash_code(code)
    else:
        return jsonify({'error': 'Unsupported language'}), 400

    # Log the code execution
    log_task_execution(user_id, language, code, result.get('output', ''), result.get('status', 'error'))

    # Ensure the result is sent back to the frontend
    return jsonify(result)

def init_user(username):
    try:
        # Check if user already exists
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

def create_or_fetch_session():
    user_id = session.get('user_id')
    if not user_id:
        logging.error("User ID not found in session.")
        # Redirect the user to profile creation or emit error
        return jsonify({"error": "User not logged in. Please create a profile."}), 401  # Unauthorized response
    
    session_data = Session.query.filter_by(user_id=user_id, start_time=datetime.utcnow().date()).first()
    if not session_data:
        session_data = Session(user_id=user_id, topic="Default", model_used="gpt-2")
        db.session.add(session_data)
        db.session.commit()
    return session_data.id

    
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

        # Check provider and generate response from the model
        if provider == 'openai':
            logging.debug('Using OpenAI model')
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
            logging.debug('Using Google model')
            if not model.startswith('models/') and not model.startswith('tunedModels/'):
                model = 'models/' + model

            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)

            if hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
                return {'code': response_text}
            else:
                return {'error': 'No valid response from Google API'}

        elif provider in ['local', 'gpt-2-local']:
            # Handle local GPT-2 model
            logging.debug('Using Local GPT-2 model')
            inputs = gpt2_tokenizer(prompt, return_tensors='pt')
            max_new_tokens = config.get('max_new_tokens', 100)
            outputs = gpt2_model.generate(**inputs, max_new_tokens=max_new_tokens)
            decoded_output = gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
            return {'code': decoded_output}

        # Extract code block from LLM response and execute
        extracted_code = extract_code_from_message(content)
        if extracted_code:
            language = "python"  # Set language; could be detected based on the model’s context
            execution_result = execute_code(extracted_code, language=language)
            return {'code': execution_result.get('output', 'Code execution failed')}

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
