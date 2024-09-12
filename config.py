import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_MODEL = "gpt-4o"  # Default OpenAI model
    GOOGLE_MODEL = "models/gemini-1.5-pro"  # Default Google Gemini model
    TEMPERATURE = 0.7
    MAX_TOKENS = 5000
    TOP_P = 1.0
    SYSTEM_PROMPT = "You are a helpful assistant."

    # Explicitly use the absolute path to your SQLite file to avoid confusion with instance folder
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI') or f'sqlite:///{os.path.join(basedir, "data", "oais.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
