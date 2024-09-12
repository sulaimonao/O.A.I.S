from transformers import GPT2Tokenizer, GPT2LMHeadModel
import torch

# Load GPT-2 model and tokenizer
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')

# Ensure the model is in evaluation mode
model.eval()

def gpt2_restructure_prompt(prompt):
    """Generate a restructured prompt using GPT-2."""
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(inputs['input_ids'], max_length=100, num_return_sequences=1)
    restructured_prompt = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return restructured_prompt

#might need to downgrade numpy
#pip install numpy<2
