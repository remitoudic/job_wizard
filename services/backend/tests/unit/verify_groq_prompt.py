
import asyncio
import os
import json
import httpx
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent

# Hardcoded for standalone verification (using env var now)
API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = "llama-3.3-70b-versatile"
BASE_URL = "https://api.groq.com/openai/v1"

SYSTEM_PROMPT = (
    "You are a professional career coach. Generate a cover letter body following this EXACT structure:\n"
    "1. Salutation (e.g. 'Dear Hiring Manager,')\n"
    "2. Opening: State role and company.\n"
    "3. Body Paragraphs: 2-3 paragraphs highlighting relevance of candidate skills to requirements.\n"
    "4. Closing: Professional sign-off.\n"
    "5. Signature: 'Sincerely,' followed by the candidate's name on a new line.\n\n"
    "Constraints:\n"
    "- Tone: Formal and business-appropriate.\n"
    "- Length: 200–400 words.\n"
    "- Content: Clarity and impact. No verbosity.\n"
    "- Formatting: Plain text only. NO markdown. NO headings. NO meta commentary."
)

USER_PROMPT = """Write a professional cover letter for John Doe applying to TechCorp as Software Engineer.

IMPORTANT: 
1. If you don't know the candidate's name, DO NOT use a placeholder like "[Your Name]". Start directly with the address/salutation.
2. DO NOT use placeholders for date like "[Date]".
3. Return ONLY the letter body. Do not use markdown code blocks or introductory text.
4. Use a very formal tone.
5. Keep the letter between 200 and 400 words.
6. Maintain a formal, business-appropriate tone.
7. finish with "Sincerely," or "Best regards," and the candidate's name.

"""

# Hook to fix Groq compatibility issue (unexpected service_tier field)
async def strip_service_tier_hook(response: httpx.Response):
    if response.status_code == 200:
        try:
            await response.aread()
            if b"service_tier" in response.content:
                data = response.json()
                if "service_tier" in data:
                    del data["service_tier"]
                    response._content = json.dumps(data).encode("utf-8")
        except Exception:
            pass

async def verify_prompt():
    print(f"🚀 Verifying Groq Model Prompt Adherence: {MODEL_NAME}...")
    
    http_client = httpx.AsyncClient(
        event_hooks={"response": [strip_service_tier_hook]}
    )
    
    provider = OpenAIProvider(
        base_url=BASE_URL, 
        api_key=API_KEY,
        http_client=http_client
    )
    model = OpenAIChatModel(model_name=MODEL_NAME, provider=provider)
    agent = Agent(
        model, 
        system_prompt=SYSTEM_PROMPT
    )
    
    try:
        result = await agent.run(USER_PROMPT)
        # Try to access data, if not try other common attributes
        if hasattr(result, 'data'):
            output = result.data
        else:
            output = str(result.data) if hasattr(result, 'data') else str(result.output) if hasattr(result, 'output') else str(result)
            
        print("\n✅ Response Received:\n" + "="*40 + "\n" + output + "\n" + "="*40)
        
        # Simple checks
        if "Here is" in output or "```" in output:
            print("\n❌ FAILED: Extra text or code blocks detected.")
        else:
            word_count = len(output.split())
            print(f"\n📊 Word Count: {word_count}")
            
            if 200 <= word_count <= 400:
                 print("✅ PASSED: Word count within range (200-400).")
            else:
                 print(f"⚠️ WARNING: Word count {word_count} is outside range (200-400).")
                 
            print("✅ PASSED: Output looks clean.")
            
    except Exception as e:
        print(f"\n❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_prompt())
