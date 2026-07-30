from datetime import timedelta
import logging

from google.protobuf.duration_pb2 import Duration
from temporalio.api.workflowservice.v1 import (
    DescribeNamespaceRequest,
    RegisterNamespaceRequest,
)
from temporalio.client import Client
from temporalio.service import RPCError, RPCStatusCode

from app.core.config import settings

logger = logging.getLogger(__name__)


async def ensure_namespace(host: str, namespace: str, retention_days: int) -> None:
    """Create the Temporal namespace if it does not already exist."""
    if namespace == "default":
        return

    admin_client = await Client.connect(host, namespace="default")
    try:
        await admin_client.workflow_service.describe_namespace(
            DescribeNamespaceRequest(namespace=namespace)
        )
        logger.info(f"Temporal namespace '{namespace}' already exists")
        return
    except RPCError as e:
        if e.status != RPCStatusCode.NOT_FOUND:
            raise

    retention = Duration()
    retention.FromTimedelta(timedelta(days=retention_days))
    try:
        await admin_client.workflow_service.register_namespace(
            RegisterNamespaceRequest(
                namespace=namespace,
                workflow_execution_retention_period=retention,
                description="Job Wizard cover letter workflows",
            )
        )
        logger.info(
            f"Created Temporal namespace '{namespace}' "
            f"(retention={retention_days}d)"
        )
    except RPCError as e:
        # Another process may have created it concurrently
        if e.status == RPCStatusCode.ALREADY_EXISTS:
            logger.info(f"Temporal namespace '{namespace}' already exists")
        else:
            raise


class TemporalClient:
    _instance = None
    _client = None

    @classmethod
    async def get_client(cls) -> Client:
        if cls._client is None:
            try:
                await ensure_namespace(
                    settings.TEMPORAL_HOST,
                    settings.TEMPORAL_NAMESPACE,
                    settings.TEMPORAL_RETENTION_DAYS,
                )
                cls._client = await Client.connect(
                    settings.TEMPORAL_HOST, namespace=settings.TEMPORAL_NAMESPACE
                )
                logger.info(f"Connected to Temporal at {settings.TEMPORAL_HOST}")
            except Exception as e:
                logger.error(f"Failed to connect to Temporal: {e}")
                raise e
        return cls._client


async def get_temporal_client() -> Client:
    return await TemporalClient.get_client()
