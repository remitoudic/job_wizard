import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def base_provider_config():
    """Standard provider config for tests that need remote agents."""
    return {
        "name": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": "fake-key",
        "model_1": "llama-3.3-70b-versatile",
        "model_2": "openai/gpt-oss-120b"
    }


@pytest.fixture
def nvidia_config():
    """NVIDIA NIM provider config."""
    return {
        "name": "nvidia",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": "nvapi-fake-key",
        "model_1": "meta/llama-4-maverick-17b-128e-instruct"
    }


def _make_mock_agent(output_text="Mock Result", delay=0.05, fail=False, error_msg="Agent failed"):
    """Helper to create a mock agent with configurable behavior."""
    agent = MagicMock()

    async def run_fn(*args, **kwargs):
        await asyncio.sleep(delay)
        if fail:
            raise Exception(error_msg)
        mock_result = MagicMock()
        mock_result.output = output_text
        mock_result.usage.return_value = MagicMock(
            request_tokens=100, response_tokens=200, total_tokens=300
        )
        return mock_result

    agent.run = AsyncMock(side_effect=run_fn)
    return agent


def _make_semaphore_mock():
    """Create a mock semaphore that allows local agent through."""
    sem = MagicMock()
    sem.locked.return_value = False
    sem.__aenter__ = AsyncMock(return_value=None)
    sem.__aexit__ = AsyncMock(return_value=None)
    return sem


# --- Test: NVIDIA provider config ---

def test_nvidia_provider_config_with_key():
    """Verify get_nvidia_config returns correct structure when key is set."""
    with patch("app.services.platform.llm_provider_service.settings") as mock_settings:
        mock_settings.NVIDIA_API_KEY = "nvapi-test-key"
        mock_settings.NVIDIA_MODEL_1 = "meta/llama-4-maverick-17b-128e-instruct"

        from app.services.platform.llm_provider_service import LLMProviderService
        service = LLMProviderService()

        config = service.get_nvidia_config()
        assert config is not None
        assert config["name"] == "nvidia"
        assert config["base_url"] == "https://integrate.api.nvidia.com/v1"
        assert config["api_key"] == "nvapi-test-key"
        assert config["model_1"] == "meta/llama-4-maverick-17b-128e-instruct"


def test_nvidia_provider_config_without_key():
    """Verify get_nvidia_config returns None when key is empty."""
    with patch("app.services.platform.llm_provider_service.settings") as mock_settings:
        mock_settings.NVIDIA_API_KEY = ""

        from app.services.platform.llm_provider_service import LLMProviderService
        service = LLMProviderService()

        config = service.get_nvidia_config()
        assert config is None


# --- Test: NVIDIA joins the race ---

@pytest.mark.asyncio
async def test_nvidia_joins_race(base_provider_config, nvidia_config):
    """Verify NVIDIA task is created and participates when API key is set."""
    with patch("app.services.cover_letter.llm_service.create_writing_agent") as mock_create:
        from app.services.cover_letter.llm_service import LLMService

        # Track which agents were created
        created_agents = []

        def agent_factory(model_name, **kwargs):
            agent = _make_mock_agent(output_text=f"Result from {model_name}", delay=0.05)
            created_agents.append(model_name)
            return agent

        mock_create.side_effect = agent_factory

        service = LLMService()
        service.local_writer = _make_mock_agent("Local Result", delay=0.1)
        service.ollama_semaphore = _make_semaphore_mock()

        # Provider returns base config + nvidia config
        service.provider_service = MagicMock()
        service.provider_service.get_provider_config.return_value = base_provider_config
        service.provider_service.get_nvidia_config.return_value = nvidia_config

        result_text, source, alt_id = await service.generate_cover_letter(
            job_description="Test job",
            job_title="Engineer",
            company="TestCorp",
            requirements=["Python"],
            job_id="test-nvidia-joins",
            user_name="Test User"
        )

        # NVIDIA model should have been created via the factory
        assert "meta/llama-4-maverick-17b-128e-instruct" in created_agents
        assert result_text is not None
        assert alt_id is not None


@pytest.mark.asyncio
async def test_nvidia_skipped_without_key(base_provider_config):
    """Verify NVIDIA is not added when API key is missing."""
    with patch("app.services.cover_letter.llm_service.create_writing_agent") as mock_create:
        from app.services.cover_letter.llm_service import LLMService

        created_agents = []

        def agent_factory(model_name, **kwargs):
            agent = _make_mock_agent(output_text=f"Result from {model_name}", delay=0.05)
            created_agents.append(model_name)
            return agent

        mock_create.side_effect = agent_factory

        service = LLMService()
        service.local_writer = _make_mock_agent("Local Result", delay=0.05)
        service.ollama_semaphore = _make_semaphore_mock()

        service.provider_service = MagicMock()
        service.provider_service.get_provider_config.return_value = base_provider_config
        service.provider_service.get_nvidia_config.return_value = None  # No key

        result_text, source, alt_id = await service.generate_cover_letter(
            job_description="Test job",
            job_title="Engineer",
            company="TestCorp",
            requirements=["Python"],
            job_id="test-nvidia-skip",
            user_name="Test User"
        )

        # NVIDIA model should NOT be in created agents
        assert "meta/llama-4-maverick-17b-128e-instruct" not in created_agents
        assert result_text is not None


@pytest.mark.asyncio
async def test_nvidia_wins_race(base_provider_config, nvidia_config):
    """Verify NVIDIA can win the race when it responds fastest."""
    with patch("app.services.cover_letter.llm_service.create_writing_agent") as mock_create:
        from app.services.cover_letter.llm_service import LLMService

        call_count = 0

        def agent_factory(model_name, **kwargs):
            nonlocal call_count
            call_count += 1
            if model_name == nvidia_config["model_1"]:
                # NVIDIA is fastest
                return _make_mock_agent("NVIDIA Cover Letter", delay=0.01)
            # Others are slower
            return _make_mock_agent(f"Slow result from {model_name}", delay=0.5)

        mock_create.side_effect = agent_factory

        service = LLMService()
        # Local is also slow
        service.local_writer = _make_mock_agent("Slow Local", delay=0.5)
        service.ollama_semaphore = _make_semaphore_mock()

        service.provider_service = MagicMock()
        service.provider_service.get_provider_config.return_value = base_provider_config
        service.provider_service.get_nvidia_config.return_value = nvidia_config

        result_text, source, alt_id = await service.generate_cover_letter(
            job_description="Test",
            job_title="Dev",
            company="Corp",
            requirements=[],
            job_id="test-nvidia-wins",
            user_name="Winner"
        )

        assert "Nvidia" in source
        assert "NVIDIA Cover Letter" in result_text


@pytest.mark.asyncio
async def test_nvidia_failure_doesnt_break_race(base_provider_config, nvidia_config):
    """Verify other participants still complete if NVIDIA fails."""
    with patch("app.services.cover_letter.llm_service.create_writing_agent") as mock_create:
        from app.services.cover_letter.llm_service import LLMService

        def agent_factory(model_name, **kwargs):
            if model_name == nvidia_config["model_1"]:
                # NVIDIA fails fast
                return _make_mock_agent(fail=True, error_msg="NVIDIA 503 server error", delay=0.01)
            return _make_mock_agent(f"Good result from {model_name}", delay=0.05)

        mock_create.side_effect = agent_factory

        service = LLMService()
        service.local_writer = _make_mock_agent("Local Success", delay=0.05)
        service.ollama_semaphore = _make_semaphore_mock()

        service.provider_service = MagicMock()
        service.provider_service.get_provider_config.return_value = base_provider_config
        service.provider_service.get_nvidia_config.return_value = nvidia_config

        result_text, source, alt_id = await service.generate_cover_letter(
            job_description="Test",
            job_title="Dev",
            company="Corp",
            requirements=[],
            job_id="test-nvidia-fail",
            user_name="User"
        )

        # Race still produces a winner from non-NVIDIA participants
        assert result_text is not None
        assert "Nvidia" not in source  # NVIDIA failed, shouldn't be winner
