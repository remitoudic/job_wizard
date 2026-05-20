"""
Groq Provider Integration Tests

This test verifies that the system is correctly configured to use Groq as the primary
LLM provider. It checks the provider settings, base URLs, and model identifiers
to ensure that the 'Groq-first' strategy is properly initialized in the application's
LLMService.
"""

import pytest
from app.services.cover_letter.llm_service import LLMService


@pytest.mark.asyncio
async def test_groq_integration_connectivity():
    """
    Integration test verifying that LLMService is configured to try Groq first.
    This test runs against the real service logic but checks configuration/priority.
    """
    service = LLMService()

    # 1. Verify Default Provider is Groq
    active_config = service.provider_service.get_provider_config()
    assert active_config["name"] == "groq", "Primary provider should be Groq"
    assert "api.groq.com" in active_config["base_url"]

    # 2. Verify Models are correct
    assert active_config["model_1"] == "llama-3.3-70b-versatile"

    print("\n✅ Groq Configuration Verified")
