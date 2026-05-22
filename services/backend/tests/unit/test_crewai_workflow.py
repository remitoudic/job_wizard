"""
Unit tests for the CrewAI Cover Letter Workflow.
These tests verify that the agents, tasks, and crew are constructed
correctly and that the generation function executes the workflow
and returns the expected output without making actual API calls.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.cover_letter.crewai_workflow import run_crewai_generation, get_llm_for_agent


def test_get_llm_for_agent():
    """
    Test that the LLM is initialized correctly with the provided temperature
    and dynamic config from the llm_provider_service.
    """
    with patch("app.services.cover_letter.crewai_workflow.llm_provider_service") as mock_provider:
        mock_provider.get_provider_config.return_value = {
            "name": "groq",
            "model_1": "test-model",
            "api_key": "test-key",
            "base_url": "https://api.test.com",
        }
        
        llm = get_llm_for_agent(temperature=0.7)
        
        # Verify ChatOpenAI initialization parameters
        assert llm.model_name == "test-model"
        assert llm.temperature == 0.7
        # Handle both SecretStr and string types based on LangChain version
        api_key_val = llm.openai_api_key.get_secret_value() if hasattr(llm.openai_api_key, 'get_secret_value') else llm.openai_api_key
        assert api_key_val == "test-key"


def test_run_crewai_generation_success():
    """
    Test the successful execution of the CrewAI workflow.
    Mocks the Crew kickoff to avoid real LLM API calls and verifies
    that all parameters are correctly passed to the workflow.
    """
    mock_result = MagicMock()
    mock_result.__str__.return_value = "This is the final polished cover letter."

    with patch("app.services.cover_letter.crewai_workflow.Crew") as mock_crew_class, \
         patch("app.services.cover_letter.crewai_workflow.get_llm_for_agent") as mock_get_llm:
         
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value = mock_llm_instance
        
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance
        
        # Call the workflow
        result = run_crewai_generation(
            job_description="We need a senior Python engineer.",
            job_title="Senior Python Engineer",
            company="Tech Corp",
            requirements=["Python", "FastAPI"],
            user_name="Jane Doe",
            user_skills="Python, Django, FastAPI",
            context_text="I have 10 years of experience.",
            language="english"
        )
        
        # Verify the result is returned as a string
        assert result == "This is the final polished cover letter."
        
        # Verify Crew was instantiated with 3 agents and 3 tasks
        mock_crew_class.assert_called_once()
        crew_kwargs = mock_crew_class.call_args.kwargs
        assert len(crew_kwargs["agents"]) == 3
        assert len(crew_kwargs["tasks"]) == 3
        assert crew_kwargs["process"].name == "sequential"
        
        # Verify kickoff was called
        mock_crew_instance.kickoff.assert_called_once()

        # Verify get_llm_for_agent was called with the specific temperatures (0.1, 0.7, 0.3)
        calls = mock_get_llm.call_args_list
        temperatures = [call.kwargs.get("temperature") for call in calls]
        assert 0.1 in temperatures
        assert 0.7 in temperatures
        assert 0.3 in temperatures
