import os
import json
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from openai import OpenAI
import google.generativeai as genai
from config import Config
from tools.intent_parser import parse_intent, handle_write_to_file, handle_execute_code
from tools.code_execution import execute_code
from tools.file_operations import read_file, write_file

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

logging.basicConfig(level=logging.DEBUG)

#Configure OAI GPT
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

def generate_code_via_llm(prompt, model, provider, config):
    try:
        # Set default values from Config.py if not provided
        temperature = config.get('temperature', Config.TEMPERATURE)
        max_tokens = config.get('maxTokens', Config.MAX_TOKENS)
        top_p = config.get('topP', Config.TOP_P)

        if provider == 'openai':
            response = client.chat.completions.with_raw_response.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,  # Use the value from config or default
                max_tokens=max_tokens,
                top_p=top_p
            )
            # Log the request ID for tracking
            logging.debug(f"OpenAI Request ID: {response.headers.get('x-request-id')}")

            # Parse the response to get the completion
            completion = response.parse()
            code = completion['choices'][0]['message']['content']
        elif provider == 'google':
            # Google API logic
            if not model.startswith('models/') and not model.startswith('tunedModels/'):
                model = 'models/' + model
            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)
            code = response.text
        else:
            return {'error': 'Unsupported provider'}
        return {'code': code}
    except Exception as e:
        logging.error(f'Error generating code: {str(e)}')
        return {'error': str(e)}

@socketio.on('message')
def handle_message(data):
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

    intent = parse_intent(message)
    
    if intent == "write_to_file":
        # Use the LLM to generate the content dynamically
        content_response = generate_code_via_llm(message, model, provider, config)
        if 'code' in content_response:
            content = content_response['code']
            result = handle_write_to_file(message, content)
            emit('message', {'user': message, 'result': result})
            logging.debug(f"Emitting write_to_file result: {result}")
        else:
            emit('message', {'user': message, 'error': content_response['error']})
            logging.error(f'Error generating content: {content_response["error"]}')
    elif intent == "execute_code":
        code_response = generate_code_via_llm(message, model, provider, config)
        if 'code' in code_response:
            result = handle_execute_code(message, code_response['code'])
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
            emit('message', {'user': message, 'code': code_response['code'], 'result': result})
            logging.debug(f'Emitting code response: {code_response["code"]}')
        else:
            emit('message', {'user': message, 'error': code_response['error']})
            logging.error(f'Error emitting code response: {code_response["error"]}')
    elif provider == 'openai':
        history = [{"role": "system", "content": Config.SYSTEM_PROMPT}]
        history.append({"role": "user", "content": message})
        # Handle OpenAI streaming response
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=history,
                max_tokens=config.get('maxTokens', Config.MAX_TOKENS),
                temperature=config.get('temperature', Config.TEMPERATURE),
                top_p=config.get('topP', Config.TOP_P),
                stream=True  # Stream the response
            )

            content = ""
            for chunk in stream:
                content_chunk = getattr(chunk.choices[0].delta, "content", None)
                if content_chunk:  # Only append content if it's not None
                    content += content_chunk
                    emit('message', {'assistant': content_chunk})  # Emit each chunk progressively
                    logging.debug(f'Streaming response chunk: {content_chunk}')

            history.append({"role": "assistant", "content": content})
            logging.debug(f'Final OpenAI Response: {content}')
            emit('message_end')  # Signal that the streaming has finished

        except Exception as e:
            logging.error(f'Error with OpenAI: {str(e)}')
            emit('message', {'error': str(e)})

    elif provider == 'google':
        try:
            genai_model = genai.GenerativeModel(model)
            if filename:
                filepath = os.path.join('uploads', filename)
                file = genai.upload_file(filepath)
                response = genai_model.generate_content([message, file])
            else:
                response = genai_model.generate_content(message)

            content = response.text
            logging.debug(f'Google Response: {content}')
            
            # Emit the full Google response at once (since it's non-streaming)
            emit('message', {'assistant': content})
            logging.debug(f'Emitting assistant response: {content}')
            
            emit('message_end')  # Signal the end of the message
            
        except Exception as e:
            logging.error(f'Error with Google: {str(e)}')
            emit('message', {'error': str(e)})


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('virtual_workspace'):
        os.makedirs('virtual_workspace')
    socketio.run(app, debug=True)
