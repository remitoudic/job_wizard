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


def test_valid_nvidia_model_configured():
    """Test that the configured NVIDIA model is in our list of known-valid models."""
    settings = get_settings()

    # List of known valid models on NVIDIA NIM that we have verified
    # If adding a new model to config.py, it must be added here and verified to exist
    # on https://build.nvidia.com/explore/discover
    verified_models = [
        "meta/llama-3.1-70b-instruct",
        "meta/llama3-70b-instruct",
        "google/gemma-2-27b-it",
        "google/gemma-2-9b-it",
        "mistralai/mistral-large-2-instruct",
        "nvidia/nemotron-4-340b-instruct",
        "meta/llama-4-maverick-17b-128e-instruct",
        "qwen/qwen2.5-coder-32b-instruct",
        "z-ai/glm-5.2",
        "deepseek-ai/deepseek-v4-pro",
        "qwen/qwen3-next-80b-a3b-instruct",
        "poolside/laguna-xs-2.1",
        "mistralai/mistral-medium-3.5-128b",
        "meta/llama-3.1-8b-instruct",
        "google/gemma-2-2b-it",
    ]

    assert settings.NVIDIA_MODEL_1 in verified_models, (
        f"Configured NVIDIA model '{settings.NVIDIA_MODEL_1}' is not in the verified list! "
        "If you are changing the model, please verify it exists on Nvidia NIM and update this test."
    )

    if settings.NVIDIA_MODEL_2:
        assert settings.NVIDIA_MODEL_2 in verified_models, (
            f"Configured NVIDIA model '{settings.NVIDIA_MODEL_2}' is not in the verified list! "
            "If you are changing the model, please verify it exists on Nvidia NIM and update this test."
        )

    if settings.NVIDIA_MODEL_3:
        assert settings.NVIDIA_MODEL_3 in verified_models, (
            f"Configured NVIDIA model '{settings.NVIDIA_MODEL_3}' is not in the verified list! "
            "If you are changing the model, please verify it exists on Nvidia NIM and update this test."
        )
