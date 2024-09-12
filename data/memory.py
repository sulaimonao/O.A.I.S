from data.models import User, Session, Interaction  # Update the path to point to the correct module

def retrieve_memory(user_id, session_id=None):
    if session_id:
        # Short-term memory for current session
        interactions = Interaction.query.filter_by(session_id=session_id).all()
    else:
        # Long-term memory for the user
        interactions = Interaction.query.join(Session).filter(Session.user_id == user_id).all()

    # Process interactions for relevant memory data
    return interactions
