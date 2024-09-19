import pickle

# Load the saved model from the pickle file
with open('/O.A.I.S./models/wordllama_model.pkl', 'rb') as file:
    model_data = pickle.load(file)

# Access the embeddings and tokenizer
embeddings = model_data['embeddings']
tokenizer = model_data['tokenizer']
config = model_data['config']

print(f"Loaded model with dimension: {config['dim']} and binary: {config['binary']}")
