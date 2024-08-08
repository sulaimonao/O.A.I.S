import logging

def validate_response(response_data, provider):
    if provider == 'openai':
        # OpenAI-specific validation: Ensure the content is a string
        return isinstance(response_data.get('content'), str)
    elif provider == 'google':
        # Google-specific validation: Ensure the content is a string
        content = response_data.get('content')
        if isinstance(content, str):
            return True
        else:
            logging.error("Google response content is not a string.")
            return False
    else:
        return False
