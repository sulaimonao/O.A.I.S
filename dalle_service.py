from flask import Flask, request, jsonify
import openai
from config import Config

app = Flask(__name__)
openai.api_key = Config.OPENAI_API_KEY

IMAGE_SIZES = {
    'square': '1024x1024',
    'tall': '1024x1792',
    'wide': '1792x1024'
}

@app.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get('prompt')
    ratio = data.get('ratio', 'square').lower()

    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    if ratio not in IMAGE_SIZES:
        return jsonify({'error': f"Invalid ratio '{ratio}' specified. Valid options are 'square', 'tall', or 'wide'."}), 400

    image_size = IMAGE_SIZES[ratio]

    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size=image_size
        )
        image_url = response['data'][0]['url']
        return jsonify({'image_url': image_url})
    except openai.error.OpenAIError as e:
        return jsonify({'error': f"OpenAI API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
