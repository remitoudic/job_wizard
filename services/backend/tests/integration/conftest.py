"""Override session-level fixtures so integration tests can run without PostgreSQL."""

import pytest


@pytest.fixture(scope="session", autouse=True)
def db_init():
    """No-op: each integration test creates its own SQLite DB via test_db fixture."""
    yield


@pytest.fixture(autouse=True)
async def manage_pubsub():
    """No-op: integration tests don't need PubSub."""
    yield
