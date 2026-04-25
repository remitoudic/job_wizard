"""
conftest.py for the tests/unit/ directory.

Overrides the session-level db_init and manage_pubsub fixtures from the
parent conftest so that pure unit tests (e.g. nginx config, PDF margin checks)
can run without a live Postgres or Redis connection.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def db_init():
    """
    No-op override: unit tests don't need a database connection.
    The parent conftest.py tries to create DB tables; that fails outside Docker.
    """
    yield


@pytest.fixture(autouse=True)
async def manage_pubsub():
    """
    No-op override: unit tests don't need the PubSub manager.
    """
    yield
