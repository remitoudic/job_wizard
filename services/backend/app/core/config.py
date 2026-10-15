import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    # LLM Settings
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"

    ENVIRONMENT: str = os.getenv(
        "ENVIRONMENT", "development"
    )  # "development" or "production"

    OPENROUTER_API_KEY: str = ""

    # Database Settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://jobwizard:jobwizard007@postgres:5432/jobwizard"
    )

    # Models Source of Truth
    # Models Source of Truth
    OPENROUTER_MODEL: str = os.getenv(
        "OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free"
    )
    OPENROUTER_MODEL_2: str = os.getenv(
        "OPENROUTER_MODEL_2", "nvidia/nemotron-3-super-120b-a12b:free"
    )

    # Groq Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL_1: str = os.getenv("GROQ_MODEL_1", "openai/gpt-oss-120b")
    GROQ_MODEL_2: str = os.getenv("GROQ_MODEL_2", "qwen/qwen3.8-27b")

    # NVIDIA NIM Settings
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_MODEL_1: str = os.getenv("NVIDIA_MODEL_1", "poolside/laguna-xs-2.1")
    NVIDIA_MODEL_2: str = os.getenv(
        "NVIDIA_MODEL_2", "nvidia/nemotron-3.5-lightning-30b-a3b"
    )
    NVIDIA_MODEL_3: str = os.getenv("NVIDIA_MODEL_3", "openai/gpt-oss-20b")

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
    LOGS_DIR: Path = Path(os.getenv("LOGS_DIR", "./data/logs"))
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))
    BACKUP_DIR: Path = Path(
        os.getenv("BACKUP_DIR", "./data/backups/letters_file_backup")
    )

    # Security Settings
    SECURE_COOKIES: bool = (
        os.getenv("SECURE_COOKIES", "True").lower() == "true"
        if ENVIRONMENT == "production"
        else False
    )

    # Scraping Settings
    PROXY_FILE_PATH: str = "proxies.json"
    USE_PLAYWRIGHT: bool = True

    # Temporal Settings
    TEMPORAL_HOST: str = os.getenv("TEMPORAL_HOST", "temporal:7233")
    TEMPORAL_NAMESPACE: str = os.getenv("TEMPORAL_NAMESPACE", "jobwizard")
    TEMPORAL_RETENTION_DAYS: int = int(os.getenv("TEMPORAL_RETENTION_DAYS", "7"))

    model_config = SettingsConfigDict(
        env_file=[
            ".env",
            ".env.local",
            "../../.env",
            "../../.env.local",
        ],
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
