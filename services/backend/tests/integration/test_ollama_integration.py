"""
Ollama Provider Integration Tests

This test verifies the connectivity and configuration of the Ollama provider
within the LLMService. It checks that the local model identifiers and API
host settings are correctly initialized, ensuring that the 'local-first'
fallback capability is ready for use.
"""

import pytest
import os
from app.services.cover_letter.llm_service import LLMService


@pytest.mark.skipif(os.environ.get("CI") == "true", reason="Ollama not available in CI")
@pytest.mark.asyncio
async def test_ollama_integration_connectivity():
    """
    Integration test verifying that the local Ollama instance is reachable
    and the LLMService can initialize the local writer.
    """
    try:
        service = LLMService()

        # 1. Verify Local Agent Initialization
        assert service.local_writer is not None
        assert service.local_writer.model.model_name == service.ollama_model_name

        # 2. Verify Connectivity to Ollama Host
        # We can try a simple run.
        print(
            f"\nProbing Ollama at {service.ollama_host} with model {service.ollama_model_name}..."
        )

        # Use a very short prompt to be quick
        prompt = "Hello. Reply with 'OK'."
        result = await service.local_writer.run(prompt)

        print(f"Ollama Response: {result.output}")
        assert len(result.output) > 0

        print("\n✅ Ollama Connectivity Verified")

    except Exception as e:
        pytest.fail(f"Ollama Integration Failed: {e}")
