import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_MODEL = "gpt-4o"  # Default OpenAI model
    GOOGLE_MODEL = "models/gemini-1.5-pro"  # Default Google Gemini model
    TEMPERATURE = 0.7
    MAX_TOKENS = 50000
    TOP_P = 1.0
    SYSTEM_PROMPT = "You are a helpful assistant."
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")  # Main DB location
    SQLALCHEMY_TRACK_MODIFICATIONS = False #for optimization
