import os
import json
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from openai import OpenAI
import google.generativeai as genai
from config import Config
from tools.intent_parser import parse_intent, handle_write_to_file, handle_execute_code
from tools.code_execution import execute_code
from tools.file_operations import read_file, write_file
from tools.database import init_db, add_message, get_conversation_history, get_user_profile, set_user_profile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

logging.basicConfig(level=logging.DEBUG)

# Initialize OpenAI client
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Configure Google Gemini
genai.configure(api_key=Config.GOOGLE_API_KEY)

# Initialize the database
init_db()

# Cache for storing previously generated code and results
resource_cache = {}

@app.route('/')
def index():
    session['id'] = os.urandom(24).hex()
    return render_template('index.html')

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

def generate_code_via_llm(prompt, model, provider, config):
    cache_key = f"{provider}:{model}:{prompt}"
    if cache_key in resource_cache:
        logging.debug(f"Cache hit for prompt: {prompt}")
        return resource_cache[cache_key]

    try:
        if provider == 'openai':
            response = openai_client.Completions.create(
                prompt=prompt,
                model=model,
                temperature=config['temperature'],
                max_tokens=config['maxTokens'],
                top_p=config['topP']
            )
            code = response['choices'][0]['text']
        elif provider == 'google':
            if not model.startswith('models/') and not model.startswith('tunedModels/'):
                model = 'models/' + model
            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)
            code = response.text
        else:
            return {'error': 'Unsupported provider'}
        
        resource_cache[cache_key] = {'code': code}
        return {'code': code}
    except Exception as e:
        logging.error(f'Error generating code: {str(e)}')
        return {'error': str(e)}

@socketio.on('message')
def handle_message(data):
    session_id = session.get('id')
    user_id = session_id  # This could be enhanced to use actual user IDs in a real system

    if 'user_profile' not in session:
        session['user_profile'] = {'name': None, 'awaiting_confirmation': False}

    data = json.loads(data)
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

    add_message(session_id, user_id, 'user', message, provider)

    # Handle user introduction and confirmation
    if session['user_profile']['awaiting_confirmation']:
        if message.lower() in ['yes', 'y']:
            session['user_profile']['awaiting_confirmation'] = False
            set_user_profile(session_id, session['user_profile']['name'])
            response_message = f"Great! I will remember your name, {session['user_profile']['name']}."
            add_message(session_id, user_id, 'assistant', response_message, provider)
            emit('message', {'user': message, 'assistant': response_message})
        else:
            session['user_profile']['name'] = None
            session['user_profile']['awaiting_confirmation'] = False
            response_message = "Okay, I won't remember your name."
            add_message(session_id, user_id, 'assistant', response_message, provider)
            emit('message', {'user': message, 'assistant': response_message})
        return

    if "my name is" in message.lower():
        parts = message.lower().split("my name is", 1)
        if len(parts) > 1 and parts[1].strip():
            name = parts[1].strip().split(' ')[0]
            session['user_profile']['name'] = name
            session['user_profile']['awaiting_confirmation'] = True
            response_message = f"Did I get that right? Is your name {name}? Please reply with 'yes' or 'no'."
            add_message(session_id, user_id, 'assistant', response_message, provider)
            emit('message', {'user': message, 'assistant': response_message})
        else:
            response_message = "I didn't catch your name. Please tell me again by saying 'My name is [Your Name]'."
            add_message(session_id, user_id, 'assistant', response_message, provider)
            emit('message', {'user': message, 'assistant': response_message})
        return

    if "what is my name" in message.lower() or "do you remember me" in message.lower():
        name = session['user_profile']['name']
        if not name:
            profile = get_user_profile(session_id)
            if profile:
                name = profile[0]
                session['user_profile']['name'] = name

        if name:
            response_message = f"Your name is {name}."
        else:
            response_message = "I don't know your name. Please tell me your name by saying 'My name is [Your Name]'."
        add_message(session_id, user_id, 'assistant', response_message, provider)
        emit('message', {'user': message, 'assistant': response_message})
        return

    intent = parse_intent(message)
    
    if intent == "write_to_file":
        content_response = generate_code_via_llm(message, model, provider, config)
        if 'code' in content_response:
            content = content_response['code']
            result = handle_write_to_file(message, content)
            add_message(session_id, user_id, 'assistant', result, provider)
            emit('message', {'user': message, 'result': result})
            logging.debug(f"Emitting write_to_file result: {result}")
        else:
            emit('message', {'user': message, 'error': content_response['error']})
            logging.error(f'Error generating content: {content_response["error"]}')
    elif intent == "execute_code":
        code_response = generate_code_via_llm(message, model, provider, config)
        if 'code' in code_response:
            result = handle_execute_code(message, code_response['code'])
            add_message(session_id, user_id, 'assistant', result, provider)
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
            add_message(session_id, user_id, 'assistant', result, provider)
            emit('message', {'user': message, 'code': code_response['code'], 'result': result})
            logging.debug(f'Emitting code response: {code_response["code"]}')
        else:
            emit('message', {'user': message, 'error': code_response['error']})
            logging.error(f'Error emitting code response: {code_response["error"]}')
    else:
        history = get_conversation_history(session_id)
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

            add_message(session_id, user_id, 'assistant', content, provider)
            logging.debug(f'{provider.capitalize()} Response: {content}')
            emit('message', {'user': message, 'assistant': content})
        except Exception as e:
            logging.error(f'Error with {provider.capitalize()}: {str(e)}')
            emit('message', {'error': str(e)})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('virtual_workspace'):
        os.makedirs('virtual_workspace')
    socketio.run(app, debug=True)
