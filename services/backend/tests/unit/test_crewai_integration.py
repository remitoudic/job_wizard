"""
Integration tests for the CrewAI workflow within the LLM Service.
This tests that the CrewAI background task is successfully launched
and managed within the existing race-mode generation logic.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.cover_letter.llm_service import LLMService


@pytest.mark.asyncio
async def test_llm_service_spawns_crewai_task():
    """
    Test that the LLMService spawns the CrewAI background task
    and processes its result alongside the standard LLM race.
    """
    with (
        patch(
            "app.services.cover_letter.llm_service.create_writing_agent"
        ) as mock_create_agent,
        patch(
            "app.services.cover_letter.crewai_workflow.run_crewai_generation"
        ) as mock_run_crewai,
    ):
        # Mock the CrewAI generation to return a specific string after a small delay
        def mock_crewai_sync(*args, **kwargs):
            import time

            time.sleep(0.1)
            return "CrewAI Final Letter"

        mock_run_crewai.side_effect = mock_crewai_sync

        service = LLMService()

        # Mock Local Agent (winner of the race)
        async def succeed_fast(*args, **kwargs):
            await asyncio.sleep(0.01)
            return MagicMock(output="Local Result")

        service.local_writer = MagicMock()
        service.local_writer.run = AsyncMock(side_effect=succeed_fast)
        service.local_writer.get_name.return_value = "Ollama (local-model)"

        # Mock Remote Agents (they will be slower)
        remote_mock = MagicMock()

        async def succeed_slow(*args, **kwargs):
            await asyncio.sleep(0.2)
            return MagicMock(output="Remote Result")

        remote_mock.run = AsyncMock(side_effect=succeed_slow)
        remote_mock.get_name.return_value = "Remote"
        mock_create_agent.return_value = remote_mock

        # Setup service configs
        service.ollama_model_name = "local"
        service.provider_service = MagicMock()
        service.provider_service.get_provider_config.return_value = {
            "name": "groq",
            "model_1": "remote-1",
            "model_2": "remote-2",
            "api_key": "sk-test",
        }
        service.provider_service.get_nvidia_config.return_value = None

        # Mock semaphore to be free
        service.ollama_semaphore = MagicMock()
        service.ollama_semaphore.locked.return_value = False
        service.ollama_semaphore.__aenter__.return_value = None

        # Run the generation race
        winner_text, winner_source, alt_id = await service.generate_cover_letter(
            job_description="desc",
            job_title="title",
            company="company",
            requirements=[],
            job_id="test-integration",
            user_name="user",
        )

        # The local agent should win because it is the fastest
        assert "Local Result" in winner_text

        # Give the background tasks time to finish (Remote=0.2s, CrewAI=0.1s)
        await asyncio.sleep(0.3)

        # Verify run_crewai_generation was called
        mock_run_crewai.assert_called_once()

        # Verify the CrewAI result is stored as an alternative
        state = service.get_alternative(alt_id)
        assert state is not None
        assert state["status"] == "completed"

        alternatives = state.get("alternatives", [])

        # We should have at least the CrewAI alternative and the remote alternative
        assert len(alternatives) >= 1

        # Check if CrewAI Agency is in the sources
        sources = [alt["source"] for alt in alternatives]
        assert "CrewAI Agency" in sources

        # Check if the text matches
        crewai_alt = next(
            alt for alt in alternatives if alt["source"] == "CrewAI Agency"
        )
        assert crewai_alt["text"] == "CrewAI Final Letter"
