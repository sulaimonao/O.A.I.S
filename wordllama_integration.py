import os
import pickle
from wordllama import WordLlama

# Create a directory if it doesn't exist
save_path = os.path.expanduser('~/O.A.I.S./models')
print(f"Saving model to: {save_path}")

# Load the 1024-dimension model with binary embeddings
wl = WordLlama.load(dim=1024, binary=True)

# Optionally load another model with 256-dimension binary embeddings
wl_binary = WordLlama.load(trunc_dim=256, binary=True)

# Extract embeddings
embeddings = wl.embed(["sample text", "another text"])  # Use the model's embedding method

# Save embeddings, tokenizer, and configuration as a pickle file
model_data = {
    'embeddings': embeddings,  # Extract embeddings
    'tokenizer': wl.tokenizer,  # Save the tokenizer, if needed
    'config': {
        'dim': 1024,  # Store the configuration to reload later
        'binary': True
    }
}

# Save the model data in a pickle format
with open(os.path.join(save_path, 'wordllama_model.pkl'), 'wb') as file:
    pickle.dump(model_data, file)
