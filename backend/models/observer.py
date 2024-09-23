import os
import pickle
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from wordllama import WordLlama
from backend.tools.pruning_utils import pre_and_post_pruning_validation

# Define absolute paths
base_dir = os.path.dirname(os.path.abspath(__file__))  # This is /Users/akeemsulaimon/O.A.I.S./backend/models
local_gpt2_model_path = os.path.join(base_dir, "local_gpt2")  # Correct path without duplicating 'models'
wordllama_model_path = os.path.join(base_dir, "wordllama_model.pkl")

# Verify correct path
print(f"Local GPT-2 model path: {local_gpt2_model_path}")  # This should print the correct path

# Check required files for GPT-2 model
required_files = ['config.json', 'merges.txt', 'model.safetensors', 'vocab.json']
for file in required_files:
    if not os.path.isfile(os.path.join(local_gpt2_model_path, file)):
        raise FileNotFoundError(f"Required file {file} not found in {local_gpt2_model_path}")

# Load the GPT-2 model and tokenizer
try:
    print("Loading GPT-2 tokenizer and model from local path...")
    gpt2_tokenizer = GPT2Tokenizer.from_pretrained(
        local_gpt2_model_path, 
        local_files_only=True
    )
    gpt2_model = GPT2LMHeadModel.from_pretrained(
        local_gpt2_model_path, 
        local_files_only=True
    )
    print("GPT-2 model and tokenizer loaded successfully.")
except Exception as e:
    raise RuntimeError(f"Failed to load GPT-2 model/tokenizer: {e}")

# Set pad_token_id manually for GPT-2 (GPT-2 doesn’t have a default pad_token_id)
if gpt2_tokenizer.pad_token_id is None:
    gpt2_tokenizer.pad_token_id = gpt2_tokenizer.eos_token_id

gpt2_model.eval()

def gpt2_restructure_prompt(prompt):
    """Generate a response from GPT-2 given a prompt."""
    try:
        inputs = gpt2_tokenizer(prompt, return_tensors="pt", padding=True)
        outputs = gpt2_model.generate(
            inputs['input_ids'],
            attention_mask=inputs['attention_mask'],
            pad_token_id=gpt2_tokenizer.eos_token_id,
            max_new_tokens=50  # Set this to the desired number of new tokens to generate
        )
        return gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        print(f"Error generating response with GPT-2: {e}")
        return None

# Load the Word Llama model from pickle file
def load_wordllama_model():
    # Verify WordLlama model path
    if not os.path.exists(wordllama_model_path):
        raise FileNotFoundError(f"The WordLlama model path {wordllama_model_path} does not exist.")

    # Load the saved WordLlama model and embeddings
    try:
        with open(wordllama_model_path, 'rb') as file:
            model_data = pickle.load(file)
        
        embeddings = model_data['embeddings']
        tokenizer = model_data['tokenizer']
        config = model_data['config']
        
        print(f"Loaded WordLlama model with dimension: {config['dim']} and binary: {config['binary']}")
        return embeddings, tokenizer
    except Exception as e:
        raise RuntimeError(f"Failed to load WordLlama model: {e}")

def process_with_wordllama(prompt):
    # This function uses WordLlama to embed the input prompt and process it
    try:
        embeddings, tokenizer = load_wordllama_model()
        
        # Process the prompt (adjust this based on your use case)
        prompt_embedding = tokenizer.encode(prompt)
        # Additional processing logic (e.g., ranking, clustering)
        
        return prompt_embedding
    except Exception as e:
        print(f"Error processing with WordLlama: {e}")
        return None

def self_train_wordllama(execution_result, task_details):
    """
    Use the execution results to fine-tune WordLlama embeddings and run pre/post-pruning validation.
    """
    try:
        embeddings, tokenizer = load_wordllama_model()

        # Fine-tune embeddings based on task details (placeholder for real logic)
        updated_embeddings = fine_tune_embeddings(embeddings, execution_result, task_details)

        # Define validation tasks (these could be representative tasks based on your system's workload)
        validation_tasks = [
            "Task 1", "Task 2", "Task 3",  # Replace with real validation tasks
        ]

        # Run pre and post pruning validation
        pre_pruning_success_rate, post_pruning_success_rate, pre_pruning_time, post_pruning_time = pre_and_post_pruning_validation(
            updated_embeddings, tokenizer, validation_tasks
        )

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
        
        with open(wordllama_model_path, 'wb') as file:
            pickle.dump(model_data, file)

        print("WordLlama model updated with self-training and pruning.")
    except Exception as e:
        print(f"Error during WordLlama self-training: {e}")

def wordllama_restructure_prompt(prompt):
    """Generate a response from the Word Llama model given a prompt."""
    try:
        # Ensure wordllama_model is defined and has generate_response method
        if 'wordllama_model' in globals() and hasattr(wordllama_model, 'generate_response'):
            return wordllama_model.generate_response(prompt)
        else:
            print("WordLlama model is not correctly loaded.")
            return None
    except Exception as e:
        print(f"Error generating response with WordLlama: {e}")
        return None

# Model selection function
def generate_response(prompt, model="gpt2"):
    if model == "gpt2":
        return gpt2_restructure_prompt(prompt)
    elif model == "wordllama":
        return wordllama_restructure_prompt(prompt)
    else:
        return "Unsupported model type."

if __name__ == "__main__":
    # Test generating a response with GPT-2
    test_prompt = "Once upon a time"
    response = generate_response(test_prompt, model="gpt2")
    print(f"Generated GPT-2 response: {response}")
