import httpx
from bs4 import BeautifulSoup
from typing import Dict, List
import re
import asyncio


class JobParser:
    """Service for parsing job descriptions from URLs"""
    
    def __init__(self):
        # Use realistic, browser-like headers to reduce chance of 403 responses
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        # Retry policy
        self.max_retries = 3
        self.backoff_factor = 1  # seconds
    
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URLs to their public/canonical versions to avoid login walls.
        Especially important for LinkedIn 'recommended' or 'collections' URLs.
        """
        try:
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if "linkedin.com" in domain:
                # Check for currentJobId param
                query = parse_qs(parsed.query)
                job_id = query.get("currentJobId")
                
                if job_id and job_id[0]:
                    return f"https://www.linkedin.com/jobs/view/{job_id[0]}/"
            
            return url
        except Exception:
            # If normalization fails, just return original URL
            return url

    async def parse_url(self, url: str, cookies: str | None = None) -> Dict:
        """
        Parse job description from URL with retries and optional headless-browser fallback
        """
        # Normalize URL to avoid auth walls (e.g. LinkedIn collections)
        url = self._normalize_url(url)

        # Try with httpx and retries for transient 403/429 responses
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, "lxml")

                    # Extract job details
                    job_data = {
                        "title": self._extract_title(soup),
                        "company": self._extract_company(soup),
                        "description": self._extract_description(soup),
                        "requirements": self._extract_requirements(soup),
                        "url": url,
                    }

                    return job_data
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response is not None else None
                last_exc = e
                # Only retry on 403/429 or 5xx errors
                if status in (403, 429) or (status and 500 <= status < 600):
                    # If last attempt, break and try fallback
                    if attempt == self.max_retries:
                        break
                    wait = self.backoff_factor * (2 ** (attempt - 1))
                    await asyncio.sleep(wait)
                    continue
                raise
            except Exception as e:
                last_exc = e
                # For other errors, break immediately
                break

        # If we get here, httpx approach failed. Try headless browser fallback if available.
        try:
            content = await self._fetch_with_playwright(url, cookies=cookies)
            soup = BeautifulSoup(content, "lxml")
            job_data = {
                "title": self._extract_title(soup),
                "company": self._extract_company(soup),
                "description": self._extract_description(soup),
                "requirements": self._extract_requirements(soup),
                "url": url,
            }
            return job_data
        except ImportError:
            # Playwright not installed
            raise Exception(
                "Failed to fetch URL (403/blocked). Consider installing Playwright for a headless-browser fallback: `pip install playwright` and run `playwright install`"
            ) from last_exc
        except Exception as e:
            raise Exception(f"Failed to fetch URL after retries and browser fallback: {e}") from e

    async def _fetch_with_playwright(self, url: str, cookies: str | None = None) -> str:
        """Fetch page content using Playwright (headless browser).

        This is optional and will raise ImportError if Playwright is not installed.
        """
        try:
            from playwright.async_api import async_playwright
        except Exception:
            # Re-raise to be handled by caller
            raise ImportError("playwright not available")

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"]) 
            page = await browser.new_page()
            # Set a realistic user agent and viewport
            await page.set_user_agent(self.headers.get("User-Agent"))
            # If caller provided a cookie string, set it as an extra header so the
            # browser will send the session cookies with requests.
            if cookies:
                try:
                    await page.set_extra_http_headers({"cookie": cookies})
                except Exception:
                    # Fall through if headers cannot be set for any reason
                    pass
            await page.goto(url, timeout=30000)
            # Wait for network to be idle or for some time
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                # Fallback: short wait
                await asyncio.sleep(1)
            content = await page.content()
            await browser.close()
            return content
    
    def _find_best_container(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Find the main content container to avoid parsing nav/footers"""
        
        # 1. Try common job board selectors
        selectors = [
            ".job-description",
            "[data-job-description]",
            "#job-details",
            ".core-section-container", # LinkedIn specific
            ".job-view-content",
            "[class*='description']",
        ]
        
        for selector in selectors:
            # Look for the element, but make sure it's substantial
            candidates = soup.select(selector)
            for candidate in candidates:
                if len(candidate.get_text(strip=True)) > 200:
                    return candidate

        # 2. Try semantic tags
        for tag in ["main", "article"]:
            element = soup.find(tag)
            if element and len(element.get_text(strip=True)) > 200:
                return element
                
        # 3. Fallback to body or soup if nothing better found
        body = soup.find("body")
        return body if body else soup

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract job title from page"""
        # First try structured data / meta tags (better for sites like LinkedIn)
        sd = self._extract_structured_data(soup)
        if sd.get("title"):
            return sd["title"].strip()

        # Try Open Graph
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            return og.get("content").strip()

        # Try common selectors
        selectors = [
            "h1",
            ".job-title",
            ".jobTitle",
            "[class*='job-title']",
            "[class*='title']",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        # Fallback to page title
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True).split("|")[0].strip()
        
        return "Job Position"
    
    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extract company name from page"""
        # Structured data
        sd = self._extract_structured_data(soup)
        if sd.get("hiringOrganization"):
            org = sd.get("hiringOrganization")
            if isinstance(org, dict) and org.get("name"):
                return org.get("name").strip()
            if isinstance(org, str):
                return org.strip()

        # Open Graph / meta
        og = soup.find("meta", property="og:site_name") or soup.find("meta", property="og:publisher")
        if og and og.get("content"):
            return og.get("content").strip()

        selectors = [
            ".company-name",
            ".companyName",
            "[class*='company']",
            "[data-company]",
            ".topcard__org-name-link", # LinkedIn
            ".job-details-jobs-unified-top-card__company-name", # LinkedIn
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        # Try to extract from title
        title_tag = soup.find("title")
        if title_tag:
            parts = title_tag.get_text().split("|")
            if len(parts) > 1:
                return parts[1].strip()

        return "Company"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract job description text"""
        # Try structured data first
        sd = self._extract_structured_data(soup)
        if sd.get("description"):
            desc = sd.get("description")
            if isinstance(desc, str) and desc.strip():
                return re.sub(r'\n\s*\n', '\n\n', desc.strip())

        # Isolate the container
        container = self._find_best_container(soup)
        
        # Clean up the container (remove scripts, styles, navs inside it if any)
        # Note: We copy to avoid modifying the passed soup heavily if we need it later? 
        # But we are decomposing, so it modifies in place. 
        # _find_best_container returns a Tag from the soup.
        
        for tag in container.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Get text
        text = container.get_text(separator="\n", strip=True)
        
        # Post-processing
        text = re.sub(r'\n\s*\n', '\n\n', text) # Normalize newlines
        
        if len(text) > 100:
             return text

        # Try Open Graph / meta description as fallback if main content failed
        og = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        if og and og.get("content"):
            return og.get("content").strip()
        
        # If scoping failed and gave us too little text, fallback to main soup paragraphs
        return self._fallback_description(soup)

    def _fallback_description(self, soup: BeautifulSoup) -> str:
        """Fallback method if container extraction fails"""
        paragraphs = soup.find_all("p")
        # Filter paragraphs that are too short to be meaningful content
        valid_paragraphs = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
        text = "\n\n".join(valid_paragraphs)
        return text if text else "No description available"

    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict:
        """Extract common structured data (JSON-LD / LD+JSON) from the page.

        Returns a dict with keys like title, description, hiringOrganization, etc.
        """
        data: Dict = {}

        # JSON-LD scripts
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            try:
                import json

                payload = json.loads(s.string or "{}")
                # JSON-LD can be a list
                if isinstance(payload, list):
                    for item in payload:
                        if isinstance(item, dict) and item.get("@type") in ("JobPosting", "JobPostingSpecification", "JobPostingSchema"):
                            payload = item
                            break
                if isinstance(payload, dict):
                    t = payload.get("@type") or payload.get("type")
                    if t and ("JobPosting" in t or t == "JobPosting"):
                        # Map common fields
                        if payload.get("title"):
                            data["title"] = payload.get("title")
                        if payload.get("description"):
                            data["description"] = payload.get("description")
                        if payload.get("hiringOrganization"):
                            data["hiringOrganization"] = payload.get("hiringOrganization")
                        if payload.get("employmentType"):
                            data["employmentType"] = payload.get("employmentType")
                        if payload.get("jobLocation"):
                            data["jobLocation"] = payload.get("jobLocation")
                        return data
            except Exception:
                continue

        return data
    
    def _extract_requirements(self, soup: BeautifulSoup) -> List[str]:
        """Extract job requirements as a list"""
        requirements = []
        
        # Use the scoped container!
        container = self._find_best_container(soup)

        # Look for lists in the description
        lists = container.find_all(["ul", "ol"])
        
        for lst in lists:
            items = lst.find_all("li")
            for item in items:
                text = item.get_text(strip=True)
                # Heuristics to keep valid requirements:
                # 1. Length > 10 chars
                # 2. Doesn't contain "Apply" or "Cookie" or likely nav link words
                if text and len(text) > 10 and len(text) < 300: 
                    if not any(x in text.lower() for x in ["copyright", "privacy policy", "terms", "cookies", "all rights reserved"]):
                         requirements.append(text)
        
        # If no lists found, try to extract from description
        if not requirements:
            description = self._extract_description(soup)
            # Look for bullet points or numbered items
            lines = description.split("\n")
            for line in lines:
                line = line.strip()
                if line and (line.startswith("•") or line.startswith("-") or 
                           re.match(r'^\d+\.', line)):
                    cleaned = line.lstrip("•-0123456789. ")
                    if len(cleaned) > 10:
                        requirements.append(cleaned)
        
        return requirements[:15]  # Increased limit slightly
