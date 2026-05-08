import asyncio
import time
import os
from app.services.platform.agents import create_writing_agent
import statistics

async def benchmark_model(model_name: str, num_runs: int = 1):
    print(f"\n🚀 Benchmarking model: {model_name}")
    agent = create_writing_agent(model_name=model_name, is_remote=False)
    
    prompt = "Write a professional cover letter for a Senior Software Engineer position at a fintech company. Keep it concise (under 200 words)."
    
    latencies = []
    
    for i in range(num_runs):
        print(f"Run {i+1}/{num_runs}...", end="", flush=True)
        start_time = time.perf_counter()
        result = await agent.run(prompt)
        end_time = time.perf_counter()
        
        latency = end_time - start_time
        latencies.append(latency)
        print(f" Done in {latency:.2f}s")
        
    avg_latency = statistics.mean(latencies)
    std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0
    
    print(f"\n📊 Results for {model_name}:")
    print(f"  Average Latency: {avg_latency:.2f}s")
    print(f"  Min Latency:     {min(latencies):.2f}s")
    print(f"  Max Latency:     {max(latencies):.2f}s")
    print(f"  Std Dev:         {std_dev:.2f}s")
    
    return {
        "model": model_name,
        "avg": avg_latency,
        "min": min(latencies),
        "max": max(latencies)
    }

async def main():
    # We test the new model
    new_model = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
    
    results = []
    try:
        results.append(await benchmark_model(new_model))
    except Exception as e:
        print(f"Error benchmarking {new_model}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
