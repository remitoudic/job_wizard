import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.pubsub import pubsub_manager

from database_pkg import init_db

@pytest.fixture(scope="session", autouse=True)
def db_init():
    """Ensure the database tables are created before any tests run."""
    init_db()

@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def manage_pubsub():
    """Ensure the PubSubManager is started and stopped for each test."""
    await pubsub_manager.start()
    yield
    await pubsub_manager.stop()

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client for FastAPI."""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://testserver"
    ) as client:
        yield client
