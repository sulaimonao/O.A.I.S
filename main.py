import os
import json
import requests
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

def generate_code_via_llm(prompt, model, provider):
    try:
        if provider == 'openai':
            response = openai_client.Completions.create(
                prompt=prompt,
                model=model
            )
            code = response['choices'][0]['text']
        elif provider == 'google':
            response = genai.generate_text(
                model=model,
                prompt=prompt
            )
            code = response.result
        else:
            return {'error': 'Unsupported provider'}
        return {'code': code}
    except Exception as e:
        return {'error': str(e)}

@socketio.on('message')
def handle_message(data):
    data = json.loads(data)
    message = data['message']
    model = data['model']
    provider = data['provider']
    filename = data.get('filename')
    print(f'Message: {message}, Model: {model}, Provider: {provider}, Filename: {filename}')
    
    if "generate code" in message.lower():
        code_response = generate_code_via_llm(message, model, provider)
        if 'code' in code_response:
            emit('message', {'user': message, 'code': code_response['code']})
        else:
            emit('message', {'user': message, 'error': code_response['error']})
    elif provider == 'openai':
        history = [{"role": "system", "content": "You are a helpful assistant."}]
        history.append({"role": "user", "content": message})
        try:
            response = openai_client.Chat.completions.create(
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
            else:
                emit('message', {'user': message, 'assistant': content})
        except Exception as e:
            emit('message', {'error': str(e)})
    elif provider == 'google':
        try:
            if filename:
                filepath = os.path.join('uploads', filename)
                file = genai.upload_file(filepath)
                response = genai.generate_text(
                    model=model,
                    prompt=[message, file]
                )
            else:
                response = genai.generate_text(
                    model=model,
                    prompt=message
                )
            content = response.result
            if "generate image" in message.lower():
                image_response = generate_image_via_llm(content, model, provider)
                if 'image_url' in image_response:
                    emit('message', {'user': message, 'assistant': content, 'image_url': image_response['image_url']})
                else:
                    emit('message', {'user': message, 'assistant': content, 'error': image_response['error']})
            else:
                emit('message', {'user': message, 'assistant': content})
        except Exception as e:
            emit('message', {'error': str(e)})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, debug=True)
