"""
Test the three-way race for cover letter generation
"""
import pytest
import asyncio
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_three_way_race():
    """Test that all three models participate in the race"""
    service = LLMService()
    
    # Verify all three agents are initialized
    assert service.local_writer is not None, "Local writer should be initialized"
    assert service.remote_writer is not None, "Remote writer 1 should be initialized"
    assert service.remote_writer_2 is not None, "Remote writer 2 should be initialized"
    
    # Verify model names
    assert service.ollama_model_name == "llama3.2:1b"
    assert service.openrouter_model_name == "xiaomi/mimo-v2-flash:free"
    assert service.openrouter_model_name_2 == "meta-llama/llama-3.3-70b-instruct:free"
    
    print(f"\n✅ Three agents initialized:")
    print(f"   1. Local: {service.ollama_model_name}")
    print(f"   2. Remote 1: {service.openrouter_model_name}")
    print(f"   3. Remote 2: {service.openrouter_model_name_2}")
    
    # Test actual race
    result, winner, alt_id = await service.generate_cover_letter(
        job_description="We are looking for a Python developer",
        job_title="Python Developer",
        company="Test Company",
        requirements=["Python", "FastAPI", "Docker"],
        user_name="Test User",
        user_skills="Python, FastAPI, Docker, PostgreSQL"
    )
    
    assert result is not None, "Cover letter should be generated"
    assert winner is not None, "Winner should be identified"
    assert len(result) > 0, "Cover letter should not be empty"
    
    print(f"\n🏁 Race completed!")
    print(f"   Winner: {winner}")
    print(f"   Cover letter length: {len(result)} characters")
    
    # Wait a bit for alternatives to complete
    if alt_id:
        print(f"\n⏳ Waiting for alternatives to complete...")
        await asyncio.sleep(10)
        
        alternatives = service.get_alternative(alt_id)
        if alternatives:
            print(f"   Alternatives completed: {len(alternatives)}")
            for alt in alternatives:
                print(f"   - {alt['source']}")
    
    print("\n✅ Three-way race test passed!")


if __name__ == "__main__":
    asyncio.run(test_three_way_race())
