import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JELLYFIN_HOST = os.environ.get('JELLYFIN_HOST')
    JELLYFIN_USERNAME = os.environ.get('JELLYFIN_USERNAME')
    JELLYFIN_PASSWORD = os.environ.get('JELLYFIN_PASSWORD')
    # Periodicity in days, default to 7 (1 week)
    PERIODICITY_DAYS = int(os.environ.get('PERIODICITY_DAYS', 7))
    # Number of periods to go back on first launch
    INITIAL_HISTORY_PERIODS = int(os.environ.get('INITIAL_HISTORY_PERIODS', 4))
    
    OLLAMA_HOST = os.environ.get('OLLAMA_HOST')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3')
    
    # Directory to store generated newsletters
    NEWSLETTER_DIR = os.path.join(os.getcwd(), 'newsletters')
