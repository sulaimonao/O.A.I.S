import openai
import google.generativeai as genai
from config import Config

def generate_code_via_llm(message, model, provider, config):
    if provider == 'openai':
        return generate_code_openai(message, model, config)
    elif provider == 'google':
        return generate_code_google(message, model, config)
    else:
        return {'error': 'Unsupported provider'}

def generate_code_openai(message, model, config):
    try:
        response = openai.Completion.create(
            engine=model,
            prompt=message,
            max_tokens=config.get('maxTokens', Config.MAX_TOKENS),
            temperature=config.get('temperature', Config.TEMPERATURE),
            top_p=config.get('topP', Config.TOP_P),
            n=1,
            stop=None
        )
        code = response.choices[0].text.strip()
        return {'code': code}
    except Exception as e:
        return {'error': str(e)}

def generate_code_google(message, model, config):
    try:
        genai_model = genai.GenerativeModel(model)
        response = genai_model.generate_content(message)
        code = response.text.strip()
        return {'code': code}
    except Exception as e:
        return {'error': str(e)}
