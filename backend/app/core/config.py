
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # LLM Settings
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2:0.5b"
    
    OPENROUTER_API_KEY: str = ""
    
    # Models Source of Truth
    # Models Source of Truth
    OPENROUTER_MODEL: str = "arcee-ai/trinity-mini:free"
    OPENROUTER_MODEL_2: str = "qwen/qwen3-next-80b-a3b-instruct:free"

    # Groq Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL_1: str = "llama-3.3-70b-versatile"
    GROQ_MODEL_2: str = "moonshotai/kimi-k2-instruct-0905"

    # LlamaCloud Settings (CV Parsing)
    LLAMA_CLOUD_API_KEY: str = ""

    # App Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Vite a Job! API"
    
    # Scraping Settings
    PROXY_FILE_PATH: str = "proxies.json"
    USE_PLAYWRIGHT: bool = True
    
    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env", "../.env.local", "../.env"],
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
