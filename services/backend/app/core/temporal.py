from temporalio.client import Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class TemporalClient:
    _instance = None
    _client = None

    @classmethod
    async def get_client(cls) -> Client:
        if cls._client is None:
            try:
                cls._client = await Client.connect(
                    settings.TEMPORAL_HOST,
                    namespace=settings.TEMPORAL_NAMESPACE
                )
                logger.info(f"Connected to Temporal at {settings.TEMPORAL_HOST}")
            except Exception as e:
                logger.error(f"Failed to connect to Temporal: {e}")
                raise e
        return cls._client

async def get_temporal_client() -> Client:
    return await TemporalClient.get_client()
