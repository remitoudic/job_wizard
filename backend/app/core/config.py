
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # LLM Settings
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    
    OPENROUTER_API_KEY: str = ""
    
    # Models Source of Truth
    OPENROUTER_MODEL: str = "google/gemma-3-27b-it:free"
    OPENROUTER_MODEL_2: str = "meta-llama/llama-3.3-70b-instruct:free"

    # App Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Job Wizard API"
    
    class Config:
        env_file = [".env", "../.env"]
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
