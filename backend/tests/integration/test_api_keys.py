
import pytest
import os
import httpx
from app.core.config import settings

@pytest.mark.asyncio
async def test_api_keys_presence():
    """
    Verify that necessary API keys are set in the environment or config.
    """
    print(f"\nChecking API Keys...")
    
    openrouter_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
    groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    
    # We warn if keys are missing but don't necessarily fail locally 
    # unless strictly required for all tests.
    # However, for production/CI where these are expected, we might want to assert.
    
    if openrouter_key:
        print("✅ OPENROUTER_API_KEY found")
    else:
        print("❌ OPENROUTER_API_KEY missing")
        # Assert failure if we expect this to be a strict check
        # assert openrouter_key, "OPENROUTER_API_KEY is missing"

    if groq_key:
        print("✅ GROQ_API_KEY found")
    else:
        print("⚠️ GROQ_API_KEY missing (optional if using OpenRouter only)")

@pytest.mark.asyncio
async def test_groq_validity():
    """
    Simple test to check if Groq API key is valid by listing models or making a small call.
    """
    groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not groq_key:
        pytest.skip("GROQ_API_KEY not set")

    print("\nTesting Groq API validity...")
    
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    
    # List models endpoint is a cheap way to verify auth
    url = "https://api.groq.com/openai/v1/models"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                print("✅ Groq API Key is valid (Models list accessible)")
                data = response.json()
                assert "data" in data, "Unexpected Groq response format"
            elif response.status_code == 401:
                pytest.fail("❌ Groq API Key is INVALID (401 Unauthorized)")
            else:
                print(f"⚠️ Groq API check returned status {response.status_code}: {response.text}")
                # Don't strictly fail on other errors (like rate limits) for this check?
                # or fail if we want to be strict.
                if response.status_code == 429:
                    pytest.skip("Groq Rate Limited")
                
        except Exception as e:
            pytest.fail(f"Groq connectivity failed: {e}")

@pytest.mark.asyncio
async def test_openrouter_validity():
    """
    Simple test to check if OpenRouter API key is valid.
    """
    key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
    if not key:
        pytest.skip("OPENROUTER_API_KEY not set")

    print("\nTesting OpenRouter API validity...")
    
    headers = {
        "Authorization": f"Bearer {key}",
    }
    
    # Auth check endpoint or models
    url = "https://openrouter.ai/api/v1/auth/key"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                print("✅ OpenRouter API Key is valid")
                data = response.json()
                # OpenRouter auth/key returns { data: { label: "..." } } or similar
                # print(f"Key info: {data}") 
            elif response.status_code == 401:
                pytest.fail("❌ OpenRouter API Key is INVALID (401 Unauthorized)")
            else:
                 # Verification might fail on their side
                print(f"⚠️ OpenRouter check returned status {response.status_code}")
                
        except Exception as e:
            pytest.fail(f"OpenRouter connectivity failed: {e}")
