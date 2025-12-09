import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    MODEL_NAME = "gpt-4o"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    @staticmethod
    def validate():
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
