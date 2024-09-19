from data.models import User, Session, Interaction  # Update the path to point to the correct module
from models.wordllama_observer import process_with_wordllama
from tools.pruning_utils import prune_wordllama_embeddings, get_importance_scores, should_prune_based_on_size
from models.wordllama_observer import process_with_wordllama, load_wordllama_model
import numpy as np

def retrieve_memory(user_id, session_id=None, task_type=None):
    query = Interaction.query
    if session_id:
        query = query.filter_by(session_id=session_id)
    else:
        query = query.join(Session).filter(Session.user_id == user_id)
    
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