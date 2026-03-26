import asyncio
import json
import httpx
import time

# Load proxies from the file
INPUT_FILE = "uploads/proxies_uploaded.json"
OUTPUT_FILE = "proxies.json" # Overwrite with good ones
TEST_URL = "http://www.google.com" # Fast reliable target
TIMEOUT = 5

async def check_proxy(proxy_data):
    # Support different field names
    ip = proxy_data.get("ip") or proxy_data.get("proxy_address")
    port = proxy_data.get("port")
    username = proxy_data.get("username")
    password = proxy_data.get("password")
    
    # We only support HTTP/HTTPS for now
    protocols = proxy_data.get("protocols", [])
    protocol = proxy_data.get("protocol")
    if protocol:
        if isinstance(protocol, list):
            protocols.extend(protocol)
        else:
            protocols.append(protocol)
    
    # Normalize protocols
    protocols = [p.lower() for p in protocols]
    if protocols and not any(p in ["http", "https"] for p in protocols):
         return None

    if not ip or not port:
        return None

    # Construct Proxy URL
    if username and password:
        proxy_url = f"http://{username}:{password}@{ip}:{port}"
    else:
        proxy_url = f"http://{ip}:{port}"
    
    try:
        start = time.time()
        async with httpx.AsyncClient(proxy=proxy_url, timeout=TIMEOUT) as client:
            response = await client.get(TEST_URL)
            if response.status_code == 200:
                latency = (time.time() - start) * 1000
                print(f"✅ {proxy_url} - {latency:.2f}ms")
                proxy_data["latency_checked"] = latency
                return proxy_data
            else:
                print(f"❌ {proxy_url} - Status {response.status_code}")
    except Exception as e:
        print(f"❌ {proxy_url} - {type(e).__name__}: {str(e)}")
        pass
    
    return None

async def main():
    print(f"Loading proxies from {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "r") as f:
            proxies = json.load(f)
    except FileNotFoundError:
        print("Proxy file not found!")
        return

    print(f"Found {len(proxies)} proxies. Testing...")
    
    tasks = [check_proxy(p) for p in proxies]
    results = await asyncio.gather(*tasks)
    
    valid_proxies = [r for r in results if r is not None]
    
    # Sort by latency
    valid_proxies.sort(key=lambda x: x.get("latency_checked", 9999))
    
    print(f"\nCompleted! Found {len(valid_proxies)} working proxies out of {len(proxies)}.")
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(valid_proxies, f, indent=4)
    
    print(f"Saved working proxies to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
