import logging
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# Load the GPT-2 model and tokenizer from the local directory
local_model_path = "./models/local_gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(local_model_path)
model = GPT2LMHeadModel.from_pretrained(local_model_path)

# Set pad_token_id manually (GPT-2 doesn't have a default pad_token_id)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token_id = tokenizer.eos_token_id

model.eval()

def gpt2_restructure_prompt(prompt):
    """Generate a restructured prompt using GPT-2."""
    logging.debug("GPT-2 model invoked for prompt restructuring.")  # Log GPT-2 invocation
    
    inputs = tokenizer(prompt, return_tensors="pt", padding=True)  # Force padding for safe measure
    attention_mask = inputs['input_ids'].ne(tokenizer.pad_token_id).long()  # Ensure no NoneType error
    
    outputs = model.generate(
        inputs['input_ids'], 
        attention_mask=attention_mask, 
        pad_token_id=tokenizer.eos_token_id,  # Set pad token ID
        max_length=100, 
        num_return_sequences=1
    )
    
    restructured_prompt = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return restructured_prompt
