"""
Cover Letter Generation Benchmark

Measures race performance with mocked agents to report timing statistics
and win distribution across providers (including NVIDIA).

Usage:
    python -m pytest tests/unit/benchmark_generation.py -v -s
"""

import asyncio
import time
import random
import statistics
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


def _make_mock_agent(output_text="Benchmark Result", delay=0.0, jitter=0.05):
    """Create a mock agent with realistic random latency."""
    agent = MagicMock()

    async def run_fn(*args, **kwargs):
        actual_delay = delay + random.uniform(0, jitter)
        await asyncio.sleep(actual_delay)
        mock_result = MagicMock()
        mock_result.output = output_text
        mock_result.usage.return_value = MagicMock(
            request_tokens=150, response_tokens=250, total_tokens=400
        )
        return mock_result

    agent.run = AsyncMock(side_effect=run_fn)
    return agent


def _make_semaphore_mock():
    sem = MagicMock()
    sem.locked.return_value = False
    sem.__aenter__ = AsyncMock(return_value=None)
    sem.__aexit__ = AsyncMock(return_value=None)
    return sem


PROVIDER_LATENCIES = {
    "local": {"delay": 0.15, "jitter": 0.1},
    "groq_1": {"delay": 0.05, "jitter": 0.08},
    "groq_2": {"delay": 0.06, "jitter": 0.09},
    "nvidia": {"delay": 0.04, "jitter": 0.07},
}


@pytest.mark.asyncio
async def test_benchmark_generation_race():
    """
    Benchmark: Run the generation race N times and report statistics.

    This uses mocked agents with realistic latency distributions to simulate
    the race between Local, Groq (x2), and NVIDIA participants.
    """
    NUM_RUNS = 10
    results = []
    win_counts = {}

    base_config = {
        "name": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": "fake-key",
        "model_1": "llama-3.3-70b-versatile",
        "model_2": "openai/gpt-oss-120b",
    }
    nvidia_config = {
        "name": "nvidia",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": "nvapi-fake-key",
        "model_1": "meta/llama-4-maverick-17b-128e-instruct",
    }

    for run in range(NUM_RUNS):
        with patch(
            "app.services.cover_letter.llm_service.create_writing_agent"
        ) as mock_create:
            from app.services.cover_letter.llm_service import LLMService

            def agent_factory(model_name, **kwargs):
                if model_name == nvidia_config["model_1"]:
                    cfg = PROVIDER_LATENCIES["nvidia"]
                elif model_name == base_config["model_1"]:
                    cfg = PROVIDER_LATENCIES["groq_1"]
                elif model_name == base_config["model_2"]:
                    cfg = PROVIDER_LATENCIES["groq_2"]
                else:
                    cfg = PROVIDER_LATENCIES["local"]
                return _make_mock_agent(
                    output_text=f"Cover letter from {model_name}",
                    delay=cfg["delay"],
                    jitter=cfg["jitter"],
                )

            mock_create.side_effect = agent_factory

            service = LLMService()
            local_cfg = PROVIDER_LATENCIES["local"]
            service.local_writer = _make_mock_agent(
                "Local cover letter",
                delay=local_cfg["delay"],
                jitter=local_cfg["jitter"],
            )
            service.ollama_semaphore = _make_semaphore_mock()

            service.provider_service = MagicMock()
            service.provider_service.get_provider_config.return_value = base_config
            service.provider_service.get_nvidia_config.return_value = nvidia_config

            start = time.perf_counter()
            text, source, alt_id = await service.generate_cover_letter(
                job_description="We are looking for a Python developer...",
                job_title="Senior Python Developer",
                company="BenchmarkCorp",
                requirements=["Python", "FastAPI", "Docker"],
                job_id=f"bench-{run}",
                user_name="Benchmark User",
            )
            elapsed = time.perf_counter() - start

            results.append({"run": run + 1, "source": source, "elapsed": elapsed})
            win_counts[source] = win_counts.get(source, 0) + 1

    # --- Report ---
    times = [r["elapsed"] for r in results]
    avg = statistics.mean(times)
    med = statistics.median(times)
    mn = min(times)
    mx = max(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0

    print("\n" + "=" * 60)
    print("  COVER LETTER GENERATION BENCHMARK REPORT")
    print("=" * 60)
    print(f"  Runs:      {NUM_RUNS}")
    print(f"  Average:   {avg * 1000:.1f} ms")
    print(f"  Median:    {med * 1000:.1f} ms")
    print(f"  Min:       {mn * 1000:.1f} ms")
    print(f"  Max:       {mx * 1000:.1f} ms")
    print(f"  Std Dev:   {stdev * 1000:.1f} ms")
    print("-" * 60)
    print("  WIN DISTRIBUTION:")
    for source, count in sorted(win_counts.items(), key=lambda x: -x[1]):
        pct = (count / NUM_RUNS) * 100
        bar = "█" * int(pct / 5)
        print(f"    {source:<45} {count:>2} ({pct:.0f}%) {bar}")
    print("-" * 60)
    print("  PER-RUN DETAIL:")
    for r in results:
        print(
            f"    Run {r['run']:>2}: {r['elapsed'] * 1000:>7.1f} ms  →  {r['source']}"
        )
    print("=" * 60)

    # Assertions
    assert len(results) == NUM_RUNS
    assert avg < 1.0, f"Average generation too slow: {avg:.3f}s"
