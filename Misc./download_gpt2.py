import os
from transformers import GPT2LMHeadModel, GPT2Tokenizer

def download_and_save_model(model_name: str, save_directory: str):
    """
    Downloads the specified GPT-2 model and tokenizer and saves them locally.

    Args:
        model_name (str): Name of the GPT-2 model variant (e.g., 'gpt2', 'gpt2-medium').
        save_directory (str): Absolute or relative path where the model and tokenizer will be saved.
    """
    try:
        # Convert to absolute path
        save_directory = os.path.abspath(save_directory)
        
        # Create the directory if it doesn't exist
        os.makedirs(save_directory, exist_ok=True)
        print(f"Saving model and tokenizer to: {save_directory}")
        
        # Download the model and tokenizer
        print(f"Downloading model '{model_name}'...")
        model = GPT2LMHeadModel.from_pretrained(model_name)
        print(f"Downloading tokenizer for '{model_name}'...")
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        
        # Save the model and tokenizer locally
        print("Saving model...")
        model.save_pretrained(save_directory)
        print("Saving tokenizer...")
        tokenizer.save_pretrained(save_directory)
        
        print("Download and save completed successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    local_model_path = "backend/models/local_gpt2"
    model_name = "gpt2"  # or another variant like "gpt2-medium"
    download_and_save_model(model_name, local_model_path)
