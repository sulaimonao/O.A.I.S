import os
import pickle
from wordllama import WordLlama

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

# Example of using the function
if __name__ == "__main__":
    prompt = "Analyze this sentence."
    result = process_with_wordllama(prompt)
    print(f"Processed result: {result}")
