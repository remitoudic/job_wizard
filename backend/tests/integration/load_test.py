
import asyncio
import httpx
import time
import statistics

API_URL = "http://localhost:8000/api/generate-cover-letter"
CONCURRENT_USERS = 15

# Payload to simulate a request
PAYLOAD = {
    "job_description": {
        "title": "Senior Software Engineer",
        "company": "Load Test Corp",
        "description": "We are looking for a software engineer to test our scalability.",
        "requirements": ["Python", "AsyncIO", "Docker", "Cloud Scaling"],
        "url": "http://example.com/job"
    },
    "user_name": "Load Tester",
    "user_skills": "Python, Performance Testing, DevOps",
    "custom_instructions": "Make it short."
}

async def send_request(client, user_id):
    start_time = time.perf_counter()
    try:
        print(f"[User {user_id}] Sending request...")
        response = await client.post(API_URL, json=PAYLOAD, timeout=120.0)
        duration = time.perf_counter() - start_time
        
        if response.status_code == 200:
            data = response.json()
            source = data.get("source", "Unknown")
            print(f"✅ [User {user_id}] Success in {duration:.2f}s | Source: {source}")
            return {"status": "success", "duration": duration, "source": source}
        else:
            print(f"❌ [User {user_id}] Failed with {response.status_code} in {duration:.2f}s: {response.text[:100]}")
            return {"status": "failed", "duration": duration, "error": response.status_code}
            
    except Exception as e:
        duration = time.perf_counter() - start_time
        print(f"🔥 [User {user_id}] Error in {duration:.2f}s: {str(e)}")
        return {"status": "error", "duration": duration, "error": str(e)}

async def run_load_test():
    print(f"🚀 Starting Load Test with {CONCURRENT_USERS} concurrent users...")
    print(f"Target URL: {API_URL}")
    
    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, i) for i in range(1, CONCURRENT_USERS + 1)]
        results = await asyncio.gather(*tasks)
        
    print("\n" + "="*40)
    print("LOAD TEST RESULTS")
    print("="*40)
    
    successes = [r for r in results if r["status"] == "success"]
    failures = [r for r in results if r["status"] != "success"]
    
    print(f"Total Requests: {len(results)}")
    print(f"Successes:      {len(successes)}")
    print(f"Failures:       {len(failures)}")
    
    if successes:
        durations = [r["duration"] for r in successes]
        print(f"Avg Duration:   {statistics.mean(durations):.2f}s")
        print(f"Max Duration:   {max(durations):.2f}s")
        print(f"Min Duration:   {min(durations):.2f}s")
        
        # Analyze Sources
        sources = [r["source"] for r in successes]
        source_counts = {s: sources.count(s) for s in set(sources)}
        print("\nProvider Breakdown:")
        for source, count in source_counts.items():
            print(f"  - {source}: {count}")
            
        # Specific check for local vs remote
        local_count = sum(1 for s in sources if "Ollama" in s or "local" in s.lower())
        remote_count = len(successes) - local_count
        
        print("\nAnalysis:")
        print(f"  Local Processed:  {local_count} (Expected ~2)")
        print(f"  Cloud Failover:   {remote_count} (Expected ~{len(successes)-2})")
    
    if failures:
        print("\nFailures Details:")
        for f in failures:
            print(f"  - {f}")

if __name__ == "__main__":
    asyncio.run(run_load_test())
