
import asyncio
import httpx
from app.services.proxy_manager import ProxyManager
import logfire

# Disable logfire sending for this test
logfire.configure(send_to_logfire=False)

async def check_proxy_quality():
    pm = ProxyManager()
    
    for i in range(5):
        proxy = pm.get_next_proxy()
        if not proxy: continue
        
        print(f"\nTesting Proxy {i+1}: {proxy}")
        test_url = "http://ip-api.com/json"
        
        try:
            async with httpx.AsyncClient(proxy=proxy, timeout=10) as client:
                response = await client.get(test_url)
                data = response.json()
                print(f"  IP: {data.get('query')}")
                print(f"  ISP: {data.get('isp')}")
                print(f"  Org: {data.get('org')}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_proxy_quality())
