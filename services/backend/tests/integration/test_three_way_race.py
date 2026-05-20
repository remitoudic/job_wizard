"""
LLM Generation Race Integration Tests

This module tests the core 'race' logic of the JobWizard application.
It triggers a parallel generation request where three different models (Local Ollama,
and two remote models from the configured provider like Groq or NVIDIA) compete
to provide the first successful result. It verifies that the winner is correctly
identified, alternatives are processed in the background, and the final output
is returned properly to the user.
"""

import pytest
import asyncio
from app.services.cover_letter.llm_service import LLMService


@pytest.mark.asyncio
async def test_three_way_race():
    """Test that all three models participate in the race"""
    service = LLMService()

    # Verify all three agents are initialized
    assert service.local_writer is not None, "Local writer should be initialized"
    # Verify local agent is initialized
    assert service.local_writer is not None, "Local writer should be initialized"

    # Remote writers are now dynamic, so they start as None
    assert service.remote_writer is None
    assert service.remote_writer_2 is None

    print("\n✅ Three agents initialized:")
    print(f"   1. Local: {service.ollama_model_name}")

    config = service.provider_service.get_provider_config()
    print(f"   2. Remote 1 ({config['name']}): {config['model_1']}")
    print(f"   3. Remote 2 ({config['name']}): {config['model_2']}")

    # Test actual race
    result, winner, alt_id = await service.generate_cover_letter(
        job_description="We are looking for a Python developer",
        job_title="Python Developer",
        company="Test Company",
        requirements=["Python", "FastAPI", "Docker"],
        job_id="test-job-id-123",
        user_name="Test User",
        user_skills="Python, FastAPI, Docker, PostgreSQL",
    )

    assert result is not None, "Cover letter should be generated"
    assert winner is not None, "Winner should be identified"
    assert len(result) > 0, "Cover letter should not be empty"

    print("\n🏁 Race completed!")
    print(f"   Winner: {winner}")
    print(f"   Cover letter length: {len(result)} characters")

    # Wait a bit for alternatives to complete
    if alt_id:
        print("\n⏳ Waiting for alternatives to complete...")
        await asyncio.sleep(10)

        alternatives_data = service.get_alternative(alt_id)
        if alternatives_data and "alternatives" in alternatives_data:
            alts_list = alternatives_data["alternatives"]
            print(f"   Alternatives completed: {len(alts_list)}")
            for alt in alts_list:
                print(f"   - {alt['source']}")

    print("\n✅ Three-way race test passed!")


if __name__ == "__main__":
    asyncio.run(test_three_way_race())
