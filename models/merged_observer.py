
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import pickle

# Load the GPT-2 model and tokenizer
local_gpt2_model_path = "./models/local_gpt2"
gpt2_tokenizer = GPT2Tokenizer.from_pretrained(local_gpt2_model_path)
gpt2_model = GPT2LMHeadModel.from_pretrained(local_gpt2_model_path)

# Set pad_token_id manually for GPT-2 (GPT-2 doesn’t have a default pad_token_id)
if gpt2_tokenizer.pad_token_id is None:
    gpt2_tokenizer.pad_token_id = gpt2_tokenizer.eos_token_id

gpt2_model.eval()

def gpt2_restructure_prompt(prompt):
    """Generate a response from GPT-2 given a prompt."""
    inputs = gpt2_tokenizer(prompt, return_tensors="pt")
    outputs = gpt2_model.generate(**inputs)
    return gpt2_tokenizer.decode(outputs[0], skip_special_tokens=True)

# Load the Word Llama model from pickle file
wordllama_model_path = "./models/wordllama_model.pkl"
with open(wordllama_model_path, "rb") as f:
    wordllama_model = pickle.load(f)

def wordllama_restructure_prompt(prompt):
    """Generate a response from the Word Llama model given a prompt."""
    return wordllama_model.generate_response(prompt)

# Model selection function
def generate_response(prompt, model="gpt2"):
    if model == "gpt2":
        return gpt2_restructure_prompt(prompt)
    elif model == "wordllama":
        return wordllama_restructure_prompt(prompt)
    else:
        return "Unsupported model type."
