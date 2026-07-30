import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from temporalio.service import RPCError, RPCStatusCode


@pytest.mark.asyncio
async def test_ensure_namespace_skips_default():
    from app.core.temporal import ensure_namespace

    with patch(
        "app.core.temporal.Client.connect", new_callable=AsyncMock
    ) as mock_connect:
        await ensure_namespace("temporal:7233", "default", 7)
        mock_connect.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_namespace_creates_when_missing():
    from app.core.temporal import ensure_namespace

    mock_client = AsyncMock()
    # describe raises NOT_FOUND, then register succeeds
    not_found = RPCError("not found", RPCStatusCode.NOT_FOUND, b"")
    mock_client.workflow_service.describe_namespace = AsyncMock(side_effect=not_found)
    mock_client.workflow_service.register_namespace = AsyncMock()

    with patch(
        "app.core.temporal.Client.connect",
        new_callable=AsyncMock,
        return_value=mock_client,
    ):
        await ensure_namespace("temporal:7233", "jobwizard", 7)

    mock_client.workflow_service.register_namespace.assert_awaited_once()
    request = mock_client.workflow_service.register_namespace.call_args.args[0]
    assert request.namespace == "jobwizard"


@pytest.mark.asyncio
async def test_ensure_namespace_noop_when_exists():
    from app.core.temporal import ensure_namespace

    mock_client = AsyncMock()
    mock_client.workflow_service.describe_namespace = AsyncMock(
        return_value=MagicMock()
    )
    mock_client.workflow_service.register_namespace = AsyncMock()

    with patch(
        "app.core.temporal.Client.connect",
        new_callable=AsyncMock,
        return_value=mock_client,
    ):
        await ensure_namespace("temporal:7233", "jobwizard", 7)

    mock_client.workflow_service.register_namespace.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_namespace_handles_race_already_exists():
    from app.core.temporal import ensure_namespace

    mock_client = AsyncMock()
    not_found = RPCError("not found", RPCStatusCode.NOT_FOUND, b"")
    already = RPCError("exists", RPCStatusCode.ALREADY_EXISTS, b"")
    mock_client.workflow_service.describe_namespace = AsyncMock(side_effect=not_found)
    mock_client.workflow_service.register_namespace = AsyncMock(side_effect=already)

    with patch(
        "app.core.temporal.Client.connect",
        new_callable=AsyncMock,
        return_value=mock_client,
    ):
        await ensure_namespace("temporal:7233", "jobwizard", 7)

    mock_client.workflow_service.register_namespace.assert_awaited_once()
