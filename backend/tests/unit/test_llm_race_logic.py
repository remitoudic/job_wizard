
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.services.llm_service import LLMService

@pytest.mark.asyncio
async def test_race_alternatives_with_failure():
    """
    Test that alternatives are still processed even if one model fails during the race.
    This ensures that a fast failure (e.g. timeout) from one provider doesn't stop
    us from collecting results from slower successful providers.
    """
    service = LLMService()
    
    # Mock agents
    service.local_writer = MagicMock()
    service.remote_writer = MagicMock()
    service.remote_writer_2 = MagicMock()
    
    # Setup mock behavior
    
    # Remote 1: Fast failure (Fastest model fails)
    async def fail_fast(*args, **kwargs):
        await asyncio.sleep(0.01)
        raise Exception("Remote 1 Failed")
    service.remote_writer.run = AsyncMock(side_effect=fail_fast)
    service.remote_writer.get_name.return_value = "Remote 1" 

    # Local: Medium success (The Winner)
    async def succeed_medium(*args, **kwargs):
        await asyncio.sleep(0.1)
        return MagicMock(output="Local Result")
    service.local_writer.run = AsyncMock(side_effect=succeed_medium)
    service.local_writer.get_name.return_value = "Local"

    # Remote 2: Slow success (The Alternative)
    async def succeed_slow(*args, **kwargs):
        await asyncio.sleep(0.3)
        return MagicMock(output="Remote 2 Result")
    service.remote_writer_2.run = AsyncMock(side_effect=succeed_slow)
    service.remote_writer_2.get_name.return_value = "Remote 2"
    
    # Force enable remotes in service configuration
    service.ollama_model_name = "local-model"
    service.openrouter_model_name = "remote-1"
    service.openrouter_model_name_2 = "remote-2"
    
    # Run generation
    winner_text, winner_source, alt_id = await service.generate_cover_letter(
        job_description="desc",
        job_title="title",
        company="company",
        requirements=[],
        user_name="user"
    )
    
    # Assertions for the winner
    assert winner_text == "Local Result"
    assert winner_source == "Ollama (local-model)"
    assert alt_id is not None, "Should return an alternative ID"
    
    # Wait for background alternatives to finish
    await asyncio.sleep(0.5) 
    
    # Retrieve alternatives
    result = service.get_alternative(alt_id)
    assert result is not None
    alts = result.get("alternatives", [])
    
    # Verification:
    # 1. Remote 2 must be present (success)
    has_remote_2 = any("remote-2" in a['source'] and a['status'] == 'completed' for a in alts)
    assert has_remote_2, f"Remote 2 missing from alternatives: {alts}"
    
    # 2. Remote 1 failure should ideally be recorded (or at least not cause crash)
    # Based on current implementation, failed attempts in the initial race might be added to alternatives
    has_remote_1_failure = any("remote-1" in a['source'] and a['status'] == 'failed' for a in alts)
    assert has_remote_1_failure, f"Remote 1 failure missing/not recorded: {alts}"

@pytest.mark.asyncio
async def test_race_all_fail():
    """Test behavior when all models fail"""
    service = LLMService()
    service.local_writer = MagicMock()
    service.remote_writer = MagicMock()
    service.remote_writer_2 = None # Disable third model
    
    service.local_writer.run = AsyncMock(side_effect=Exception("Local Fail"))
    service.local_writer.get_name.return_value = "Local"
    
    service.remote_writer.run = AsyncMock(side_effect=Exception("Remote Fail"))
    service.remote_writer.get_name.return_value = "Remote"
    
    service.ollama_model_name = "local"
    service.openrouter_model_name = "remote"
    
    with pytest.raises(Exception) as exc:
        await service.generate_cover_letter(
            job_description="d", job_title="t", company="c", requirements=[], user_name="u"
        )
    
    assert "All models failed" in str(exc.value)
