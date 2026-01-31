
import asyncio
import httpx
from app.services.proxy_manager import ProxyManager
import logfire

# Disable logfire
logfire.configure(send_to_logfire=False)

TEST_URL = "https://de.indeed.com/?vjk=855deef53cd3562f&advn=8743040970454369"

async def test_httpx_proxy():
    pm = ProxyManager()
    proxy = pm.get_next_proxy()
    print(f"Using Proxy: {proxy}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # Use simple httpx request with proxy
        # Verify if Oxylabs Unblocker handles the rendering/unblocking
        print(f"Fetching {TEST_URL}...")
        async with httpx.AsyncClient(proxy=proxy, timeout=60.0, follow_redirects=True, verify=False) as client:
            response = await client.get(TEST_URL, headers=headers)
            
            print(f"Status: {response.status_code}")
            print(f"Content Length: {len(response.text)}")
            
            if "Cloudflare" in response.text:
                print("⚠️ Detected Cloudflare Challenge")
            if "hCaptcha" in response.text:
                print("⚠️ Detected hCaptcha")
                
            if response.status_code == 200:
                # Save just a snippet to check title
                print(f"Preview: {response.text[:500]}")
                print("✅ HTTPX Fetch Successful!")
            else:
                print("❌ HTTPX Fetch Failed")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_httpx_proxy())
