import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    # LLM Settings
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "google/gemma-4-E2B-it"
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development") # "development" or "production"
    
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

    # NVIDIA NIM Settings
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_MODEL_1: str = os.getenv("NVIDIA_MODEL_1", "meta/llama-4-maverick-17b-128e-instruct")
    NVIDIA_MODEL_2: str = os.getenv("NVIDIA_MODEL_2", "qwen/qwen2.5-coder-32b-instruct")

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
    
    # Security Settings
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "True").lower() == "true" if ENVIRONMENT == "production" else False

    # Scraping Settings
    PROXY_FILE_PATH: str = "proxies.json"
    USE_PLAYWRIGHT: bool = True
    
    # Temporal Settings
    TEMPORAL_HOST: str = os.getenv("TEMPORAL_HOST", "temporal:7233")
    TEMPORAL_NAMESPACE: str = os.getenv("TEMPORAL_NAMESPACE", "jobwizard")
    TEMPORAL_RETENTION_DAYS: int = int(os.getenv("TEMPORAL_RETENTION_DAYS", "7"))
    
    model_config = SettingsConfigDict(
        env_file=[".env/.env.local", ".env/.env", "../../.env/.env.local", "../../.env/.env"],
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
