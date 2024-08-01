import os
import json
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from openai import OpenAI
import google.generativeai as genai
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Initialize OpenAI client
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

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

@app.route('/execute_code', methods=['POST'])
def execute_code():
    data = request.json
    code = data.get('code')
    language = data.get('language')
    if not code or not language:
        return jsonify({'error': 'Code or language not provided'})

    try:
        if language == 'python':
            result = subprocess.run(['python', '-c', code], capture_output=True, text=True)
        elif language == 'bash':
            result = subprocess.run(['bash', '-c', code], capture_output=True, text=True)
        else:
            return jsonify({'error': 'Unsupported language'})

        output = result.stdout + result.stderr
        return jsonify({'output': output})

    except Exception as e:
        return jsonify({'error': str(e)})

def generate_image_via_llm(prompt, model, provider):
    try:
        if provider == 'openai':
            response = openai_client.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']
        elif provider == 'google':
            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)
            image_url = response.text
        else:
            return {'error': 'Unsupported provider'}
        return {'image_url': image_url}
    except Exception as e:
        return {'error': str(e)}

def process_ai_instruction(instruction, model, provider):
    if "execute code" in instruction.lower():
        code = extract_code_from_instruction(instruction)
        language = detect_language_from_instruction(instruction)
        if code and language:
            return execute_code(code, language)
    return {'error': 'No executable code found'}

def extract_code_from_instruction(instruction):
    # Extract code from the instruction
    # Placeholder implementation
    return "print('Hello World!')"

def detect_language_from_instruction(instruction):
    # Detect language from the instruction
    # Placeholder implementation
    return "python"

@socketio.on('message')
def handle_message(data):
    data = json.loads(data)
    message = data['message']
    model = data['model']
    provider = data['provider']
    filename = data.get('filename')
    print(f'Message: {message}, Model: {model}, Provider: {provider}, Filename: {filename}')
    
    if provider == 'openai':
        history = [{"role": "system", "content": "You are a helpful assistant."}]
        history.append({"role": "user", "content": message})
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=history,
                max_tokens=4000,
                temperature=0.9,
                top_p=1.0
            )
            content = response['choices'][0]['message']['content']
            history.append({"role": "assistant", "content": content})
            if "generate image" in message.lower():
                image_response = generate_image_via_llm(content, model, provider)
                if 'image_url' in image_response:
                    emit('message', {'user': message, 'assistant': content, 'image_url': image_response['image_url']})
                else:
                    emit('message', {'user': message, 'assistant': content, 'error': image_response['error']})
            elif "execute code" in message.lower():
                code_response = process_ai_instruction(content, model, provider)
                if 'output' in code_response:
                    emit('message', {'user': message, 'assistant': content, 'code_output': code_response['output']})
                else:
                    emit('message', {'user': message, 'assistant': content, 'error': code_response['error']})
            else:
                emit('message', {'user': message, 'assistant': content})
        except Exception as e:
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
            if "generate image" in message.lower():
                image_response = generate_image_via_llm(content, model, provider)
                if 'image_url' in image_response:
                    emit('message', {'user': message, 'assistant': content, 'image_url': image_response['image_url']})
                else:
                    emit('message', {'user': message, 'assistant': content, 'error': image_response['error']})
            elif "execute code" in message.lower():
                code_response = process_ai_instruction(content, model, provider)
                if 'output' in code_response:
                    emit('message', {'user': message, 'assistant': content, 'code_output': code_response['output']})
                else:
                    emit('message', {'user': message, 'assistant': content, 'error': code_response['error']})
            else:
                emit('message', {'user': message, 'assistant': content})
        except Exception as e:
            emit('message', {'error': str(e)})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, debug=True)
