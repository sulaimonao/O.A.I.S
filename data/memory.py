from data.models import User, Session, Interaction  # Update the path to point to the correct module

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

