from data.models import User, Session, Interaction  # Update the path to point to the correct module
from models.wordllama_observer import process_with_wordllama

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

def log_wordllama_interaction(user_id, message):
    """
    Log WordLlama interactions in the system memory for later retrieval.
    """
    embeddings = process_with_wordllama(message)
    
    # Log the interaction with the embeddings
    log_task_execution(user_id, 'WordLlama', message, str(embeddings), 'success')
