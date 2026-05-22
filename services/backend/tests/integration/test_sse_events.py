import pytest
import asyncio
import json
import uuid
from httpx import AsyncClient
from app.core.pubsub import pubsub_manager


@pytest.mark.asyncio
async def test_sse_event_stream_order(async_client: AsyncClient):
    """
    Mock a background task that emits 3 events and verify
    the SSE endpoint receives all 3 in order.
    """
    job_id = str(uuid.uuid4())
    events_to_send = [
        {
            "job_id": job_id,
            "status": "extracting",
            "message": "Step 1: Analyzing profile",
        },
        {"job_id": job_id, "status": "generating", "message": "Step 2: Writing letter"},
        {"job_id": job_id, "status": "completed", "message": "Step 3: Done"},
    ]

    async def mock_notifier():
        # Give the event stream some time to establish connection
        await asyncio.sleep(0.5)
        for event in events_to_send:
            await pubsub_manager.notify(event)
            # Small delay to ensure order in the stream
            await asyncio.sleep(0.1)

    # Start notification task in background
    notifier_task = asyncio.create_task(mock_notifier())

    received_events = []
    try:
        # We use a 10s timeout to avoid hanging if things fail
        async with async_client.stream(
            "GET", f"/api/events/{job_id}", timeout=10.0
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    # Extract JSON from 'data: {...}'
                    payload_str = line[6:].strip()
                    if not payload_str:
                        continue

                    data = json.loads(payload_str)
                    
                    if not received_events or received_events[-1]["status"] != data["status"]:
                        received_events.append(data)

                    # SSE stream should close on 'completed' or 'error' in our implementation
                    if data["status"] in ("completed", "error"):
                        break
    finally:
        await notifier_task

    # Verification
    assert len(received_events) == 3
    for i, original in enumerate(events_to_send):
        assert received_events[i]["job_id"] == job_id
        assert received_events[i]["status"] == original["status"]
        assert received_events[i]["message"] == original["message"]


@pytest.mark.asyncio
async def test_sse_concurrency_isolation(async_client: AsyncClient):
    """
    Verify that independent jobs DON'T receive events
    intended for other jobs (Concurrency check).
    """
    job_a = str(uuid.uuid4())
    job_b = str(uuid.uuid4())

    event_a = {"job_id": job_a, "status": "completed", "message": "Job A complete"}
    event_b = {"job_id": job_b, "status": "completed", "message": "Job B complete"}

    async def notify_both():
        await asyncio.sleep(0.5)
        await pubsub_manager.notify(event_a)
        await asyncio.sleep(0.1)
        await pubsub_manager.notify(event_b)

    # Start notifier
    notifier_task = asyncio.create_task(notify_both())

    # Client A: Listen for Job A
    received_a = []
    try:
        async with async_client.stream(
            "GET", f"/api/events/{job_a}", timeout=5.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    received_a.append(data)
                    if data["status"] == "completed":
                        break
    finally:
        await notifier_task

    # Verification: Client A should ONLY have received event_a
    assert len(received_a) == 1
    assert received_a[0]["job_id"] == job_a
    assert received_a[0]["message"] == "Job A complete"

    # We don't see Job B's event in Client A's stream
    assert all(d["job_id"] != job_b for d in received_a)
