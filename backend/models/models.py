# backend/models/models.py

from .db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    profile_data = db.Column(db.JSON)  

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(120), nullable=False)  # Add this field
    start_time = db.Column(db.DateTime, default=datetime.utcnow)  # Add this field
    model_used = db.Column(db.String(50), nullable=False)  # Add this field

class Interaction(db.Model):
    __tablename__ = 'interactions'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('user_sessions.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    task_outcome = db.Column(db.String(50))
    feedback = db.Column(db.String(50))  # Add this field
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Add this field

class CodeExecutionLog(db.Model):
    __tablename__ = 'code_execution_logs'
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    language = db.Column(db.String, nullable=False)
    code = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text, nullable=True)
    status = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_input = db.Column(db.String(500))
    intent = db.Column(db.String(50))
    success = db.Column(db.Boolean)

    def __repr__(self):
        return f"<TaskHistory {self.id} - Intent {self.intent}>"


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