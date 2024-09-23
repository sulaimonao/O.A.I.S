# backend/tools/memory.py

from backend.models.models import User, UserSession, Interaction  # Corrected import
from backend.models.observer import process_with_wordllama, load_wordllama_model  # Corrected import
from backend.tools.pruning_utils import prune_wordllama_embeddings, get_importance_scores, should_prune_based_on_size  # Corrected import
from backend.tools.task_logging import log_task_execution 
import numpy as np
import os
import pickle

# Create or fetch session data
def create_or_fetch_session():
    user_id = session.get('user_id')
    if not user_id:
        logging.error("User ID not found in session.")
        return jsonify({"error": "User not logged in. Please create a profile."}), 401

    session_data = UserSession.query.filter_by(user_id=user_id, start_time=datetime.utcnow().date()).first()
    if not session_data:
        session_data = UserSession(user_id=user_id, topic="Default", model_used="gpt-2")
        db.session.add(session_data)
        db.session.commit()
    return session_data.id

def retrieve_memory(user_id, session_id=None, task_type=None):
    """
    Retrieve interactions based on user ID, session ID, and task type.
    """
    query = Interaction.query
    if session_id:
        query = query.filter_by(session_id=session_id)
    else:
        query = query.join(UserSession).filter(UserSession.user_id == user_id)
    
    # Filter by task type if provided
    if task_type:
        query = query.filter(Interaction.task_outcome == task_type)

    interactions = query.all()
    return interactions

def log_wordllama_interaction(user_id, message, task_success):
    """
    Log WordLlama interactions in the system memory and trigger pruning based on model size and task success rate.
    """
    embeddings, tokenizer = load_wordllama_model()
    wordllama_output = process_with_wordllama(message)

    # Log the interaction with the embeddings
    log_task_execution(user_id, 'WordLlama', message, str(wordllama_output), 'success')

    # Get the success rate (this should be calculated based on past task successions)
    success_rate = calculate_success_rate(user_id)  # Implement this function

    # Trigger pruning based on model size, growth rate, and success rate
    if should_prune_based_on_size(embeddings, success_rate):
        importance_scores = get_importance_scores(embeddings)
        pruned_embeddings = prune_wordllama_embeddings(embeddings, importance_scores, threshold=0.01)
        
        # Save pruned embeddings
        save_path = os.path.expanduser('~/O.A.I.S./models/wordllama_model.pkl')
        with open(save_path, 'wb') as file:
            model_data = {
                'embeddings': pruned_embeddings,
                'tokenizer': tokenizer,
                'config': {'dim': 1024, 'binary': True}
            }
            pickle.dump(model_data, file)

        print(f"Pruned and saved embeddings to {save_path}")

def calculate_success_rate(user_id):
    """
    Calculate the success rate of tasks based on past interactions.
    """
    interactions = Interaction.query.join(UserSession).filter(UserSession.user_id == user_id).all()
    if not interactions:
        return 1.0  # Default to perfect success rate if no interactions
    success_count = sum(1 for i in interactions if i.task_outcome == 'success')
    return success_count / len(interactions)
