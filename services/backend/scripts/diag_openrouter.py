import asyncio
import os
import sys
from app.services.cover_letter.llm_service import LLMService
from dotenv import load_dotenv

load_dotenv()


async def diagnose_openrouter():
    print("🔍 Starting OpenRouter Diagnostics...")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY is not set in environment!")
        return

    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "INVALID"
    print(f"🔑 API Key found: {masked_key}")

    service = LLMService()

    print(f"🤖 Model 1: {service.openrouter_model_name}")
    print(f"🤖 Model 2: {service.openrouter_model_name_2}")

    if not service.remote_writer:
        print("❌ Remote Writer 1 is NOT initialized (Check API Key or Model Name)")
    if not service.remote_writer_2:
        print("❌ Remote Writer 2 is NOT initialized")

    prompt = "Reply with 'OK' if you can read this."

    # Test Model 1
    if service.remote_writer:
        print(f"\n📡 Testing Model 1 ({service.openrouter_model_name})...")
        try:
            start = asyncio.get_event_loop().time()
            result = await service.remote_writer.run(prompt)
            duration = asyncio.get_event_loop().time() - start
            print(f"✅ Success ({duration:.2f}s): {result.output}")
        except Exception as e:
            print(f"❌ Failed: {type(e).__name__}: {e}")

    # Test Model 2
    if service.remote_writer_2:
        print(f"\n📡 Testing Model 2 ({service.openrouter_model_name_2})...")
        try:
            start = asyncio.get_event_loop().time()
            result = await service.remote_writer_2.run(prompt)
            duration = asyncio.get_event_loop().time() - start
            print(f"✅ Success ({duration:.2f}s): {result.output}")
        except Exception as e:
            print(f"❌ Failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(diagnose_openrouter())
