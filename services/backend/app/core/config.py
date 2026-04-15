import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    # LLM Settings
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2:0.5b"
    
    OPENROUTER_API_KEY: str = ""
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://jobwizard:jobwizard007@postgres:5432/jobwizard")
    
    # Models Source of Truth
    # Models Source of Truth
    OPENROUTER_MODEL: str = "arcee-ai/trinity-mini:free"
    OPENROUTER_MODEL_2: str = "qwen/qwen3-next-80b-a3b-instruct:free"

    # Groq Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL_1: str = "llama-3.3-70b-versatile"
    GROQ_MODEL_2: str = "openai/gpt-oss-120b"

    # LlamaCloud Settings (CV Parsing)
    LLAMA_CLOUD_API_KEY: str = ""

    # App Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Vite a Job! API"
    
    # Cloudinary Settings
    CLOUDINARY_URL: str = ""

    # Debugging & Logging
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PROMPT_AUDIT_LOG_ENABLED: bool = True
    LOGS_DIR: Path = Path("/app/logs")

    # Scraping Settings
    PROXY_FILE_PATH: str = "proxies.json"
    USE_PLAYWRIGHT: bool = True
    
    model_config = SettingsConfigDict(
        env_file=[".env/.env.local", ".env/.env", "../../.env/.env.local", "../../.env/.env"],
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
