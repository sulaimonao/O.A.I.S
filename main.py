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

def generate_code_via_llm(prompt, model, provider, config):
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
            # Ensure the model name starts with 'models/' or 'tunedModels/'
            if not model.startswith('models/') and not model.startswith('tunedModels/'):
                model = 'models/' + model
            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)
            code = response.text
        else:
            return {'error': 'Unsupported provider'}
        return {'code': code}
    except Exception as e:
        print(f'Error generating code: {str(e)}')
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

    print(f'Message: {message}, Model: {model}, Provider: {provider}, Filename: {filename}, Config: {config}')
    
    if "generate code" in message.lower():
        code_response = generate_code_via_llm(message, model, provider, config)
        if 'code' in code_response:
            emit('message', {'user': message, 'code': code_response['code']})
            print(f'Emitting code response: {code_response["code"]}')
        else:
            emit('message', {'user': message, 'error': code_response['error']})
            print(f'Error emitting code response: {code_response["error"]}')
    elif provider == 'openai':
        history = [{"role": "system", "content": Config.SYSTEM_PROMPT}]
        history.append({"role": "user", "content": message})
        try:
            response = openai_client.Chat.completions.create(
                model=model,
                messages=history,
                max_tokens=config.get('maxTokens', Config.MAX_TOKENS),
                temperature=config.get('temperature', Config.TEMPERATURE),
                top_p=config.get('topP', Config.TOP_P)
            )
            content = response['choices'][0]['message']['content']
            history.append({"role": "assistant", "content": content})
            print(f'OpenAI Response: {content}')
            if "generate image" in message.lower():
                image_response = generate_image_via_llm(content, model, provider, config)
                if 'image_url' in image_response:
                    emit('message', {'user': message, 'assistant': content, 'image_url': image_response['image_url']})
                    print(f'Emitting image response: {image_response["image_url"]}')
                else:
                    emit('message', {'user': message, 'assistant': content, 'error': image_response['error']})
                    print(f'Error emitting image response: {image_response["error"]}')
            else:
                emit('message', {'user': message, 'assistant': content})
                print(f'Emitting assistant response: {content}')
        except Exception as e:
            print(f'Error with OpenAI: {str(e)}')
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
            print(f'Google Response: {content}')
            if "generate image" in message.lower():
                image_response = generate_image_via_llm(content, model, provider, config)
                if 'image_url' in image_response:
                    emit('message', {'user': message, 'assistant': content, 'image_url': image_response['image_url']})
                    print(f'Emitting image response: {image_response["image_url"]}')
                else:
                    emit('message', {'user': message, 'assistant': content, 'error': image_response['error']})
                    print(f'Error emitting image response: {image_response["error"]}')
            else:
                emit('message', {'user': message, 'assistant': content})
                print(f'Emitting assistant response: {content}')
        except Exception as e:
            print(f'Error with Google: {str(e)}')
            emit('message', {'error': str(e)})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, debug=True)
