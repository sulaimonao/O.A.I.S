import os
import json
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
            emit('message', {'user': message, 'assistant': content})
        except Exception as e:
            emit('message', {'error': str(e)})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, debug=True)
