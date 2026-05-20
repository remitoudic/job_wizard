import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.cover_letter.llm_service import LLMService


@pytest.fixture
def mock_provider_service():
    # Patch the singleton instance in the service module
    with patch(
        "app.services.cover_letter.llm_service.llm_provider_service"
    ) as mock_service:
        # Default to Groq being active
        mock_service.get_active_provider.return_value = "groq"
        mock_service.get_provider_config.return_value = {
            "name": "groq",
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": "fake-key",
            "model_1": "llama-3.3-70b-versatile",
            "model_2": "openai/gpt-oss-120b",
        }
        # Reset state
        mock_service.report_rate_limit = MagicMock()
        yield mock_service


@pytest.mark.asyncio
async def test_groq_failover_trigger(mock_provider_service):
    """
    Test that when Groq fails (simulated),
    the service calls report_rate_limit for Groq and retries.
    """
    with patch(
        "app.services.cover_letter.llm_service.create_writing_agent"
    ) as mock_create_agent:
        # Mock Local Agent (success)
        mock_local_agent = MagicMock()
        mock_local_agent.run = AsyncMock(return_value=MagicMock(output="Local Result"))

        # Mock Remote Agent (Groq) - FAILS with 401/Error
        mock_remote_agent = MagicMock()
        # Simulate generic failure
        mock_remote_agent.run = AsyncMock(side_effect=Exception("401 Unauthorized"))

        mock_create_agent.side_effect = [
            mock_local_agent,
            mock_remote_agent,
            mock_remote_agent,
        ]

        service = LLMService()

        try:
            # We expect a race.
            # First attempt: Groq is active. It fails.
            # Service catches, calls report_rate_limit("groq")
            await service.generate_cover_letter(
                job_description="Job",
                job_title="Title",
                company="Comp",
                requirements=["Req"],
                job_id="test-failover",
            )
        except Exception:
            # We might fail on retry exhaustion or similar, which is fine for this test
            # as long as we verified the reporting trigger.
            pass

        # VERIFY: Did we report Groq failure?
        # Note: In actual code, "Groq failed" triggers report_rate_limit("groq")
        # Ensure we called it at least once
        mock_provider_service.report_rate_limit.assert_called_with("groq")


@pytest.mark.asyncio
async def test_groq_success(mock_provider_service):
    """
    Test successful execution with Groq
    """
    with patch(
        "app.services.cover_letter.llm_service.create_writing_agent"
    ) as mock_create_agent:
        mock_local_agent = MagicMock()
        mock_local_agent.run = AsyncMock(return_value=MagicMock(output="Local Result"))

        # Mock Remote Agent - SUCCESS
        mock_remote_agent = MagicMock()
        mock_remote_agent.run = AsyncMock(return_value=MagicMock(output="Groq Result"))

        # We need 3 agents: Local, Remote1, Remote2
        mock_create_agent.side_effect = [
            mock_local_agent,
            mock_remote_agent,
            mock_remote_agent,
        ]

        service = LLMService()

        result, source, _ = await service.generate_cover_letter(
            job_description="Job",
            job_title="Title",
            company="Comp",
            requirements=["Req"],
            job_id="test-success",
        )

        # Since it's a race, either can win.
        # But we want to verify Groq WAS attempted and didn't crash.
        # If Ollama wins, source is "Ollama (...)".
        # If Groq wins, source is "Groq (...)".
        print(f"Winner Source: {source}")
        assert "Groq" in source or "Ollama" in source
        # Verify remote agent WAS created (implying we tried Groq)
        assert mock_create_agent.call_count >= 2
