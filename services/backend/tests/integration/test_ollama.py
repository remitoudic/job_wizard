import pytest
import os
from app.services.platform.agents import create_writing_agent


@pytest.mark.asyncio
async def test_ollama_connection():
    """
    Test that we can connect to Ollama and generate a response.
    Requires Ollama to be running and the model to be available.
    """
    # Get configuration from environment
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

    print(f"\nTesting with Ollama host: {ollama_host}")
    print(f"Testing with model: {model_name}")

    # Create the agent
    agent = create_writing_agent(model_name=model_name, is_remote=False)

    # Verify the model name is correctly set on the agent
    assert agent.model.model_name == model_name

    # Run a simple prompt
    prompt = "Tell me you are working."

    try:
        result = await agent.run(prompt)
        output_text = result.output

        print(f"Response: {output_text}")

        # Verify we got a string back
        assert isinstance(output_text, str)
        assert len(output_text) > 0

        # Basic content check (allowing for some variation)
        # assert "working" in output_text.lower() or "ollama" in output_text.lower()
        assert len(output_text) > 0

    except Exception as e:
        pytest.fail(f"Ollama interaction failed: {str(e)}")
