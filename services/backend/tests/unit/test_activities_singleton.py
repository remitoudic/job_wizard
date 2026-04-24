"""
Unit tests for the activities module singleton pattern.

Regression guard for the bug where `get_llm_service()` returned a *new*
LLMService on every call, destroying shared state (semaphore, alternatives
store, provider failover).

Two tests, no repeated setup — shared via module-scoped fixtures.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import app.services.cover_letter.activities as activities_module


# ---------------------------------------------------------------------------
# Override session-scoped fixtures that require a running DB / pubsub.
# These tests are pure-unit: no DB, no network.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def db_init(request):
    """No-op override — singleton tests need no database."""
    return


@pytest.fixture(autouse=True)
async def manage_pubsub():
    """No-op override — singleton tests don't publish events."""
    yield

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_activity_singletons():
    """Guarantee a clean singleton state before and after every test."""
    activities_module._llm_service = None
    activities_module._pdf_service = None
    activities_module._backup_service = None
    yield
    activities_module._llm_service = None
    activities_module._pdf_service = None
    activities_module._backup_service = None


@pytest.fixture
def fake_llm_service():
    """A lightweight stand-in for LLMService that records instantiation count."""
    call_count = {"n": 0}

    class FakeLLMService:
        def __init__(self):
            call_count["n"] += 1
            self.alternatives_store = {}
            self.background_tasks = set()
            self.ollama_semaphore = MagicMock()
            self.ollama_semaphore.locked.return_value = False

        @property
        def instantiation_count(self):
            return call_count["n"]

    return FakeLLMService, call_count


# ---------------------------------------------------------------------------
# Test 1 — singleton identity
# ---------------------------------------------------------------------------

def test_get_llm_service_returns_same_instance(fake_llm_service):
    """
    Calling get_llm_service() multiple times MUST return the identical object.

    Before the fix this failed because every call did `return LLMService()`,
    creating a new instance (and resetting the asyncio.Semaphore, alternatives
    store, and provider failover state each time).
    """
    FakeLLMService, call_count = fake_llm_service

    with patch.object(activities_module, "LLMService", FakeLLMService):
        first  = activities_module.get_llm_service()
        second = activities_module.get_llm_service()
        third  = activities_module.get_llm_service()

    assert first is second is third, (
        "get_llm_service() must return the same object on repeated calls"
    )
    assert call_count["n"] == 1, (
        f"LLMService.__init__ was called {call_count['n']} times — must be called exactly once"
    )


# ---------------------------------------------------------------------------
# Test 2 — shared state is preserved across simulated activity calls
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_shared_state_preserved_across_activity_calls(fake_llm_service):
    """
    State written to the LLMService inside one activity call must be visible
    to the next call, proving the singleton is shared.

    This simulates the broken flow: the Temporal worker invokes
    `generate_text_race` twice (e.g. two concurrent requests).  With the old
    code, the second call got a fresh service with an empty alternatives_store
    and a fresh semaphore — losing all context from the first call.
    """
    FakeLLMService, _ = fake_llm_service

    async def fake_generate(**kwargs):
        return "Cover letter text", "FakeGroq (model-x)", "alt-42"

    with patch.object(activities_module, "LLMService", FakeLLMService):
        # Simulate first activity execution writing to alternatives_store
        svc = activities_module.get_llm_service()
        svc.alternatives_store["alt-42"] = {"status": "completed", "alternatives": []}

        # Simulate second activity execution reading the stored alternative
        svc2 = activities_module.get_llm_service()
        stored = svc2.alternatives_store.get("alt-42")

    assert svc is svc2, "Both activity calls must reference the same service instance"
    assert stored is not None, (
        "alternatives_store written in call 1 must be readable in call 2 — "
        "was None, confirming the singleton was broken"
    )
    assert stored["status"] == "completed"
