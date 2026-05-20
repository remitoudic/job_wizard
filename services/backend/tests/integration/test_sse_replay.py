import pytest
import asyncio
import json
import uuid
from httpx import AsyncClient
from app.core.pubsub import pubsub_manager


@pytest.mark.asyncio
async def test_sse_replay_after_completion(async_client: AsyncClient):
    """
    Simulate a scenario where a job completes BEFORE the client connects.
    The SSE stream should yield the terminal state immediately and close.
    """
    job_id = f"test-replay-{uuid.uuid4()}"
    completion_event = {
        "job_id": job_id,
        "status": "completed",
        "message": "Instant replay test",
    }

    # 1. Notify BEFORE client connects
    # (This should persist to the JobStatus table via our new logic)
    await pubsub_manager.notify(completion_event)

    # 2. Connect to SSE stream
    received_events = []
    try:
        # We expect this to be nearly instant because it's a replay
        async with async_client.stream(
            "GET", f"/api/events/{job_id}", timeout=5.0
        ) as response:
            assert response.status_code == 200

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    payload_str = line[6:].strip()
                    if not payload_str:
                        continue

                    data = json.loads(payload_str)
                    received_events.append(data)

                    # The stream should terminate on 'completed'
                    if data["status"] in ("completed", "error"):
                        break
    except Exception as e:
        pytest.fail(f"SSE replay failed: {e}")

    # 3. Verification
    assert len(received_events) == 1
    assert received_events[0]["job_id"] == job_id
    assert received_events[0]["status"] == "completed"
    assert received_events[0]["message"] == "Instant replay test"


@pytest.mark.asyncio
async def test_sse_sync_then_live(async_client: AsyncClient):
    """
    Simulate a job that is in progress.
    The client should receive the current state and then wait for live events.
    """
    job_id = f"test-sync-{uuid.uuid4()}"

    # 1. Partial progress BEFORE connection
    await pubsub_manager.notify(
        {"job_id": job_id, "status": "extracting", "message": "First event"}
    )

    # 2. Mock a notifier that sends the rest later
    async def mock_notifier():
        await asyncio.sleep(0.5)
        await pubsub_manager.notify(
            {"job_id": job_id, "status": "completed", "message": "Second event"}
        )

    notifier_task = asyncio.create_task(mock_notifier())

    received_events = []
    try:
        async with async_client.stream(
            "GET", f"/api/events/{job_id}", timeout=10.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    received_events.append(data)
                    if data["status"] == "completed":
                        break
    finally:
        await notifier_task

    # 3. Verification: Should have 2 events
    assert len(received_events) == 2
    assert received_events[0]["status"] == "extracting"
    assert received_events[1]["status"] == "completed"
