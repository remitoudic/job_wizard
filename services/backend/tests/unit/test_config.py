from app.core.config import Settings, get_settings

def test_settings_initialization():
    """Test that settings can be initialized without errors in Pydantic V2."""
    settings = Settings()
    assert settings.PROJECT_NAME == "Vite a Job! API"
    assert hasattr(settings, "OLLAMA_HOST")

def test_get_settings_caching():
    """Test that get_settings is properly cached."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2

def test_env_file_loading():
    """Test that env file loading config exists."""
    # We can't easily test the actual file loading without mocking or dummy files,
    # but we can verify the model config has the env_file etc.
    config = Settings.model_config
    assert "env_file" in config
    assert config.get("extra") == "ignore"
    assert config.get("case_sensitive") is True
