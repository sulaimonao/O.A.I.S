import os
import pickle
from wordllama import WordLlama
from tools.pruning_utils import pre_and_post_pruning_validation

# Load the pre-trained WordLlama model and tokenizer
model_path = os.path.expanduser('~/O.A.I.S./models/wordllama_model.pkl')

def load_wordllama_model():
    # Load the saved WordLlama model and embeddings
    with open(model_path, 'rb') as file:
        model_data = pickle.load(file)
    
    embeddings = model_data['embeddings']
    tokenizer = model_data['tokenizer']
    config = model_data['config']
    
    print(f"Loaded WordLlama model with dimension: {config['dim']} and binary: {config['binary']}")
    return embeddings, tokenizer

def process_with_wordllama(prompt):
    # This function uses WordLlama to embed the input prompt and process it
    embeddings, tokenizer = load_wordllama_model()
    
    # Process the prompt (adjust this based on your use case)
    prompt_embedding = tokenizer.encode(prompt)
    # Additional processing logic (e.g., ranking, clustering)
    
    return prompt_embedding

def self_train_wordllama(execution_result, task_details):
    """
    Use the execution results to fine-tune WordLlama embeddings and run pre/post-pruning validation.
    """
    embeddings, tokenizer = load_wordllama_model()

    # Fine-tune embeddings based on task details (placeholder for real logic)
    updated_embeddings = fine_tune_embeddings(embeddings, execution_result, task_details)

    # Define validation tasks (these could be representative tasks based on your system's workload)
    validation_tasks = [
        "Task 1", "Task 2", "Task 3",  # Replace with real validation tasks
    ]

    # Run pre and post pruning validation
    pre_pruning_success_rate, post_pruning_success_rate, pre_pruning_time, post_pruning_time = pre_and_post_pruning_validation(updated_embeddings, tokenizer, validation_tasks)

    print(f"Pre-Pruning Success Rate: {pre_pruning_success_rate}, Post-Pruning Success Rate: {post_pruning_success_rate}")
    print(f"Pre-Pruning Time: {pre_pruning_time}s, Post-Pruning Time: {post_pruning_time}s")

    # Save the final updated and pruned embeddings
    model_data = {
        'embeddings': updated_embeddings,
        'tokenizer': tokenizer,
        'config': {
            'dim': 1024,
            'binary': True
        }
    }
    
    save_path = os.path.expanduser('~/O.A.I.S./models/wordllama_model.pkl')
    with open(save_path, 'wb') as file:
        pickle.dump(model_data, file)

    print("WordLlama model updated with self-training and pruning.")
