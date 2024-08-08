import os
from dotenv import load_dotenv
import logging

# Load the environment variables from the .env file
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_MODEL = "gpt-4o"  # Default OpenAI model
    GOOGLE_MODEL = "models/gemini-1.5-pro"  # Default Google Gemini model
    TEMPERATURE = 0.9
    MAX_TOKENS = 4000
    TOP_P = 1.0
    SYSTEM_PROMPT = "You are a helpful assistant."
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE = os.path.join(BASEDIR, 'main_database.db')
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", f'sqlite:///{DATABASE}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Environment-specific configurations
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    if ENVIRONMENT == 'development':
        LOG_LEVEL = logging.DEBUG
    elif ENVIRONMENT == 'production':
        LOG_LEVEL = logging.ERROR

# Set logging configuration
logging.basicConfig(level=Config.LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
