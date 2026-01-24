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

        # 3. Fetch Content (Shared Logic)
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, "lxml")
                    
                    # 4. Extract Data (Strategy Delegate)
                    try:
                        result = parser.extract_job_data(soup, url)
                        logfire.info("Job data extracted successfully", url=url)
                        return result
                    except Exception as e:
                        logfire.error("Data extraction failed", url=url, error=str(e))
                        raise Exception(f"Could not extract job details from page: {str(e)}")

            except httpx.TimeoutException as e:
                logfire.warn("Request timeout", url=url, attempt=attempt)
                last_exc = e
                if attempt == self.max_retries:
                    raise Exception(f"Request timeout after {self.max_retries} attempts. The page may be slow or unreachable.")
                wait = self.backoff_factor * (2 ** (attempt - 1))
                await asyncio.sleep(wait)
                continue
                
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response is not None else None
                logfire.warn("HTTP error", url=url, status=status, attempt=attempt)
                last_exc = e
                
                # Provide specific error messages for common HTTP errors
                if status == 403:
                    raise Exception("Access forbidden (403). The site may require login or has blocked automated access.")
                elif status == 404:
                    raise Exception("Job posting not found (404). The URL may be incorrect or the posting may have been removed.")
                elif status == 429:
                    raise Exception("Rate limited (429). Too many requests. Please wait a moment and try again.")
                elif status and 500 <= status < 600:
                    if attempt == self.max_retries:
                        raise Exception(f"Server error ({status}). The job board's server is experiencing issues. Please try again later.")
                    wait = self.backoff_factor * (2 ** (attempt - 1))
                    await asyncio.sleep(wait)
                    continue
                else:
                    raise Exception(f"HTTP error {status}: {str(e)}")
                    
            except httpx.ConnectError as e:
                logfire.error("Connection error", url=url, error=str(e))
                raise Exception(f"Could not connect to the website. Please check the URL and your internet connection.")
                
                    
            except Exception as e:
                logfire.error("Unexpected error during fetch", url=url, error=str(e), error_type=type(e).__name__)
                raise Exception(f"Failed to fetch job URL: {str(e)}")


