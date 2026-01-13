import httpx
from bs4 import BeautifulSoup
from typing import Dict
import asyncio
from app.services.parsers import ParserRegistry
import logfire

class JobParser:
    """Service for parsing job descriptions using strategy pattern"""
    
    def __init__(self):
        # Use realistic, browser-like headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        self.max_retries = 3
        self.backoff_factor = 1

    async def parse_url(self, url: str, cookies: str | None = None) -> Dict:
        """
        Parse job description from URL using the appropriate strategy
        """
        # 1. Get Strategy
        parser = ParserRegistry.get_parser(url)
        logfire.info("Parsing job URL", url=url, strategy=parser.__class__.__name__)
        
        # 2. Normalize URL (Strategy specific)
        url = parser.normalize_url(url)

        # 3. Fetch Content (Shared Logic)
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, "lxml")
                    
                    # 4. Extract Data (Strategy Delegate)
                    return parser.extract_job_data(soup, url)

            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response is not None else None
                logfire.warn("HTTP failed", url=url, status=status, attempt=attempt)
                last_exc = e
                if status in (403, 429) or (status and 500 <= status < 600):
                    if attempt == self.max_retries:
                        break
                    wait = self.backoff_factor * (2 ** (attempt - 1))
                    await asyncio.sleep(wait)
                    continue
                raise
            except Exception as e:
                last_exc = e
                break

        # Fallback: Headless Browser
        try:
            logfire.info("Attempting Playwright fallback", url=url)
            content = await self._fetch_with_playwright(url, cookies=cookies)
            soup = BeautifulSoup(content, "lxml")
            return parser.extract_job_data(soup, url)
        except ImportError:
            raise Exception("Failed to fetch URL. Playwright fallback unavailable.") from last_exc
        except Exception as e:
            logfire.error("Parsing failed", url=url, error=str(e))
            raise Exception(f"Failed to fetch URL: {e}") from e

    async def _fetch_with_playwright(self, url: str, cookies: str | None = None) -> str:
        """Fetch page content using Playwright (headless browser)."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("Playwright library not installed. Please run 'pip install playwright'.")
        except Exception as e:
            raise ImportError(f"Failed to import Playwright: {e}")

        try:
            async with async_playwright() as pw:
                browser = None
                try:
                    browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"]) 
                except Exception as e:
                    if "executable" in str(e).lower():
                        raise Exception("Playwright browser binaries missing. Run 'playwright install chromium'.")
                    raise Exception(f"Failed to launch browser: {e}")
                
                try:
                    page = await browser.new_page(user_agent=self.headers.get("User-Agent"))
                    if cookies:
                        try:
                            await page.set_extra_http_headers({"cookie": cookies})
                        except Exception:
                            pass
                    await page.goto(url, timeout=30000)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        await asyncio.sleep(1)
                    content = await page.content()
                    return content
                finally:
                    if browser:
                        await browser.close()
        except Exception as e:
            if "Playwright" in str(e): # Preserve our custom messages
                raise
            raise Exception(f"Playwright execution failed: {e}")
