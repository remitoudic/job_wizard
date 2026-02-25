from app.services.browser_service import BrowserService
from app.services.platform.proxy_manager import ProxyManager
import asyncio
import logfire

# Configure logfire to print to console
logfire.configure(send_to_logfire='if-token-present')

async def verify():
    print("1. Testing Proxy Manager...")
    pm = ProxyManager()
    proxy = pm.get_next_proxy()
    print(f"Got proxy: {proxy}")
    
    if not proxy:
        print("❌ No proxies loaded!")
        return

    print("\n2. Testing Browser Service (IP Check)...")
    service = BrowserService()
    
    # Use a site that echoes IP
    url = "https://api.ipify.org?format=json"
    
    try:
        content = await service.fetch_page(url)
        print(f"Content fetched: {content}")
        if proxy.split(":")[1].split("/")[2] in content: # simplistic check if IP is in content
             print("✅ Proxy likely working (IP match could be verified if we parsed content)")
        else:
             print("ℹ️ Fetched content. Check if IP matches proxy.")
             
    except Exception as e:
        print(f"❌ Browser fetch failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
