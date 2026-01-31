
import pytest
import os
import asyncio
from app.services.agents import create_writing_agent
from pydantic_ai import Agent

@pytest.mark.asyncio
async def test_openrouter_connection():
    """
    Test that we can connect to OpenRouter and generate a response.
    Requires OPENROUTER_API_KEY to be set.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    # Use a cheap/free model for testing
    model_name = os.getenv("OPENROUTER_MODEL", "xiaomi/mimo-v2-flash:free")
    
    print(f"\nTesting with model: {model_name}")

    # Create the agent
    agent = create_writing_agent(model_name=model_name, is_remote=True)
    
    # Verify the model name is correctly set on the agent
    # Accessing the model name might differ based on pydantic-ai version, 
    # but based on common patterns:
    assert agent.model.model_name == model_name
    
    # Run a simple prompt
    prompt = "Hello! Please reply with 'OpenRouter is working' and nothing else."
    
    try:
        result = await agent.run(prompt)
        output_text = result.output
        
        print(f"Response: {output_text}")
        
        # Verify we got a string back
        assert isinstance(output_text, str)
        assert len(output_text) > 0
        
        # Basic content check (allowing for some variation)
        assert "working" in output_text.lower() or "openrouter" in output_text.lower()

    except Exception as e:
        pytest.fail(f"OpenRouter interaction failed: {str(e)}")
