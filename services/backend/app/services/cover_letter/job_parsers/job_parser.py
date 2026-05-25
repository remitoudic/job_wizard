import httpx
from bs4 import BeautifulSoup
from typing import Dict
import asyncio
from app.services.cover_letter.job_parsers.registry import ParserRegistry
import logfire
from app.services.platform.proxy_manager import ProxyManager


class JobParser:
    """Service for parsing job descriptions using strategy pattern"""

    def __init__(self):
        # Use realistic, browser-like headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        self.max_retries = 3
        self.backoff_factor = 1

    async def parse_url(self, url: str, cookies: str | None = None) -> Dict:
        """
        Parse job description from URL using the appropriate strategy
        """
        # 1. Get Strategy
        try:
            parser = ParserRegistry.get_parser(url)
            logfire.info("Parsing job URL", url=url, strategy=parser.__class__.__name__)
        except Exception as e:
            logfire.error("Failed to get parser strategy", url=url, error=str(e))
            raise Exception(f"Unsupported job board URL: {url}")

        # 2. Normalize URL (Strategy specific)
        try:
            url = parser.normalize_url(url)
        except Exception as e:
            logfire.error("URL normalization failed", url=url, error=str(e))
            raise Exception(f"Invalid job URL format: {str(e)}")

        # 3. Fetch Content (HTTPX)
        try:
            content = ""

            # Browser Service logic removed as per request to remove Playwright dependency.
            # We fall back to standard HTTPX request.

            if hasattr(parser, "fetch_content"):
                try:
                    # Allow parser to implement its own fetching (e.g. for bypassing protections)
                    if asyncio.iscoroutinefunction(parser.fetch_content):
                        content = await parser.fetch_content(url)
                    else:
                        content = await asyncio.to_thread(parser.fetch_content, url)
                except Exception as e:
                    logfire.warn("Custom fetch strategy failed", url=url, error=str(e))
                    # If the custom fetch specifically says "BLOCKED", re-raise it to trigger manual mode in UI
                    if "block" in str(e).lower() or "forbidden" in str(e).lower():
                        raise Exception(
                            "System is blocked by the job site. Please enter details manually."
                        )
                    # Otherwise fall through to standard HTTPX (or just fail if we want strictness)

            if not content:
                # HTTPX Fallback (Original Logic)

                # Get proxy if available
                proxy_manager = ProxyManager()
                proxy_url = proxy_manager.get_next_proxy()

                for attempt in range(1, self.max_retries + 1):
                    try:
                        async with httpx.AsyncClient(
                            follow_redirects=True,
                            timeout=60.0,
                            proxy=proxy_url,
                            verify=False,  # Required for some unblocker proxies
                        ) as client:
                            try:
                                logfire.instrument_httpx(client)
                            except Exception as le:
                                logfire.warn(
                                    "Failed to instrument httpx client", error=str(le)
                                )
                            response = await client.get(url, headers=self.headers)
                            response.raise_for_status()
                            content = response.text
                            break

                    except httpx.TimeoutException:
                        logfire.warn("Request timeout", url=url, attempt=attempt)
                        if attempt == self.max_retries:
                            raise Exception(
                                f"Request timeout after {self.max_retries} attempts."
                            )
                        wait = self.backoff_factor * (2 ** (attempt - 1))
                        await asyncio.sleep(wait)
                        continue

                    except httpx.HTTPStatusError as e:
                        status = (
                            e.response.status_code if e.response is not None else None
                        )
                        logfire.warn(
                            "HTTP error", url=url, status=status, attempt=attempt
                        )

                        if status == 403:
                            # Specific message to trigger manual mode
                            raise Exception(
                                "Access forbidden (403). System is blocked. Please enter details manually."
                            )
                        elif status == 404:
                            raise Exception("Job posting not found (404).")
                        elif status == 429:
                            raise Exception("Rate limited (429). Too many requests.")
                        elif status and 500 <= status < 600:
                            if attempt == self.max_retries:
                                raise Exception(f"Server error ({status}).")
                            wait = self.backoff_factor * (2 ** (attempt - 1))
                            await asyncio.sleep(wait)
                            continue
                        else:
                            raise Exception(f"HTTP error {status}: {str(e)}")

                    except Exception as e:
                        logfire.error(
                            "Unexpected error during fetch", url=url, error=str(e)
                        )
                        raise Exception(f"Failed to fetch job URL: {str(e)}")

            if not content:
                raise Exception("Failed to retrieve content from URL")

            # 4. Extract Data
            soup = BeautifulSoup(content, "lxml")

            try:
                result = parser.extract_job_data(soup, url)
                logfire.info("Job data extracted successfully", url=url)
                return result
            except Exception as e:
                logfire.error("Data extraction failed", url=url, error=str(e))
                raise Exception(f"Could not extract job details: {str(e)}")

        except Exception as e:
            raise e
