import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.cover_letter.llm_service import LLMService

@pytest.mark.asyncio
async def test_generate_cover_letter_with_custom_instructions():
    # Mock settings and dependencies
    with patch("app.services.cover_letter.llm_service.create_writing_agent") as mock_create_agent, \
         patch("app.services.cover_letter.llm_service.settings") as mock_settings:
        
        # Setup mock agent
        mock_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.output = "Generated Letter Body"
        mock_agent.run.return_value = mock_response
        mock_create_agent.return_value = mock_agent
        
        # Initialize service
        service = LLMService()
        
        # Mock provider service
        service.provider_service = MagicMock()
        service.provider_service.get_provider_config.return_value = {
            "name": "mock", "model_1": "mock-1", "model_2": "mock-2"
        }

        # Run generation with custom instructions
        await service.generate_cover_letter(
            job_description="Software Engineer role",
            job_title="Software Engineer",
            company="TechCorp",
            requirements=["Python"],
            custom_instructions="Include a joke about Java"
        )
        
        # Verify call args contains the custom instruction
        call_args = mock_agent.run.call_args[0][0]
        assert "CUSTOM USER GUIDANCE:" in call_args
        assert "Include a joke about Java" in call_args
