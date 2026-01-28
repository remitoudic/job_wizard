from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logfire
from typing import Optional, Dict, Any
from app.services.proxy_manager import ProxyManager
from app.core.config import settings

class BrowserService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.proxy_manager = ProxyManager()

    async def fetch_page(self, url: str) -> str:
        """
        Fetch a page using Playwright with a rotated proxy.
        Returns the HTML content of the page.
        """
        proxy_url = self.proxy_manager.get_next_proxy()
        
        logfire.info("Starting Playwright fetch", url=url, proxy=proxy_url)
        
        async with async_playwright() as p:
            # Launch options
            launch_args = {
                "headless": True,
            }
            
            # Note: Playwright handles proxies at the context level usually, or browser level.
            # Passing proxy to launch() makes it apply to the browser.
            if proxy_url:
                launch_args["proxy"] = {"server": proxy_url}

            try:
                browser = await p.chromium.launch(**launch_args)
                
                # Create context with realistic User Agent
                # TODO: Rotate User Agents too if needed, for now standardizing
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    accept_downloads=False,
                    ignore_https_errors=True
                )
                
                page = await context.new_page()
                
                # Navigate
                # Wait for load state 'domcontentloaded' or 'networkidle'
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Additional wait if needed for dynamic content
                # For Indeed, sometimes we need to wait for specific selectors
                # But 'domcontentloaded' is often enough for the initial text
                
                content = await page.content()
                
                await browser.close()
                return content

            except Exception as e:
                print(f"DEBUG: Playwright fetch failed: {type(e).__name__} - {e}")
                logfire.error("Playwright fetch failed", url=url, error=str(e))
                raise Exception(f"Failed to fetch page with browser: {str(e)}")
