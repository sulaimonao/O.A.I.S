# backend/socketio/handlers.py

from flask_socketio import emit
import json
from flask import session
from ..tools.intent_parser import parse_intent_with_gpt2, handle_task
from ..tools.memory import retrieve_memory, create_or_fetch_session
from ..tools.code_execution import generate_llm_response, execute_code
from ..models.db import db
from ..models.models import Interaction
import logging

def socketio_handlers(socketio):
    @socketio.on('message')
    def handle_message(data):
        logging.debug(f"Received data: {data}")
        data = json.loads(data)
        message = data['message']
        model = data.get('model') or session.get('model', 'gpt-4o')
        provider = data.get('provider') or session.get('provider', 'openai')
        config = data.get('config', {})

        intent = parse_intent_with_gpt2(message)

        if intent in ["create_folder", "delete_file", "create_file", "delete_folder", "execute_python_code", "execute_bash_code", "execute_js_code"]:
            result = handle_task(intent, message)
            emit('message', {'response': result})
            emit('message', {'feedback_prompt': "Was the task executed correctly? (yes/no)"})

            if session.get('memory_enabled', True):
                user_id = session.get('user_id')
                session_id = create_or_fetch_session(user_id)
                past_memory = retrieve_memory(user_id, session_id, task_type=intent)
                if past_memory:
                    emit('message', {'memory': past_memory})
                interaction = Interaction(
                    session_id=session_id,
                    prompt=message,
                    response=result,
                    task_outcome="success" if result != "Unknown intent." else "failure"
                )
                db.session.add(interaction)
                db.session.commit()

        elif intent == "feedback":
            user_feedback = message.lower()
            last_interaction = Interaction.query.order_by(Interaction.timestamp.desc()).first()
            if last_interaction:
                last_interaction.feedback = user_feedback
                db.session.commit()
                emit('message', {'response': "Thank you for the feedback!"})

        else:
            code_response = generate_llm_response(message, model, provider, config)
            if 'code' in code_response:
                if provider != 'openai':
                    emit('message', {'assistant': code_response['code']})
            else:
                emit('message', {'error': code_response['error']})

        if intent == "retrieve_memory":
            user_id = session.get('user_id')
            memory = retrieve_memory(user_id)
            emit('message', {'memory': memory})

        if intent == "system_health_check":
            health_data = system_health_check()
            emit('message', {'response': health_data})

        elif intent == "map_file_system":
            file_map = map_file_system()
            emit('message', {'response': file_map})

    @socketio.on('execute_code')
    def handle_execute_code(data):
        code = data.get('code', '')
        language = data.get('language', 'python')
        user_id = session.get('user_id', 'anonymous')

        if not code:
            emit('execute_code_response', {'error': 'No code provided'})
            return

        result = execute_code(code, language)

        # Log the execution
        # log_task_execution(user_id, language, code, result.get('output', ''), result.get('status', 'error'))

        emit('execute_code_response', result)

    @socketio.on('status_update')
    def handle_status_update():
        try:
            # Check GPT-2 status
            # Placeholder for actual status check
            gpt2_status_text = "Operational"  # Replace with actual status

            # Get WordLlama status
            wordllama_status = get_wordllama_status()

            emit('status_update', {
                'gpt2': {
                    'status': gpt2_status_text,
                    'current_task': 'Idle'
                },
                'wordllama': wordllama_status
            })
        except Exception as e:
            logging.error(f"Error during status update: {str(e)}")
