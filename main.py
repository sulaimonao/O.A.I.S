import os
import json
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from openai import OpenAI
import google.generativeai as genai
from config import Config
from tools.intent_parser import parse_intent, handle_write_to_file, handle_execute_code
from tools.file_operations import read_file, write_file

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

logging.basicConfig(level=logging.DEBUG)

# Configure OpenAI GPT
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Configure Google Gemini
genai.configure(api_key=Config.GOOGLE_API_KEY)

@app.route('/')
def index():
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

            if hasattr(response, 'candidate') and response.candidate.safety_ratings:
                logging.error("Response blocked due to safety ratings")
                return {'error': 'Response blocked due to safety ratings.'}

            return {'code': response.text}

        else:
            return {'error': 'Unsupported provider'}

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

    custom_engine = data.get('customEngine')
    if custom_engine:
        model = custom_engine

    intent = parse_intent(message)
    logging.debug(f"Intent: {intent}, Message: {message}, Model: {model}, Provider: {provider}")

    if intent == "write_to_file":
        content_response = generate_llm_response(message, model, provider, config)
        if 'code' in content_response:
            content = content_response['code']
            result = handle_write_to_file(message, content)
            emit('message', {'user': message, 'result': result})
            logging.debug(f"Emitting write_to_file result: {result}")
        else:
            emit('message', {'user': message, 'error': content_response['error']})
            logging.error(f"Error generating content: {content_response['error']}")

    elif intent == "execute_code":
        code_response = generate_llm_response(message, model, provider, config)
        if 'code' in code_response:
            result = handle_execute_code(message, code_response['code'])
            emit('message', {'user': message, 'result': result})
            logging.debug(f"Emitting execute_code result: {result}")
        else:
            emit('message', {'user': message, 'error': code_response['error']})
            logging.error(f'Error generating code: {code_response["error"]}')
    
    else:
        emit('message', {'error': 'Unknown intent'})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, debug=True)
