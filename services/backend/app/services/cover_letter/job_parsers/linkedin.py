from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any
import json
from .base import BaseParser


class LinkedInParser(BaseParser):
    """Specialized parser for LinkedIn"""

    def normalize_url(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            # Check for currentJobId param
            query = parse_qs(parsed.query)
            job_id = query.get("currentJobId")

            if job_id and job_id[0]:
                return f"https://www.linkedin.com/jobs/view/{job_id[0]}/"

            # Remove query params if it's already a view url
            if "/jobs/view/" in url:
                return url.split("?")[0]

            return url
        except Exception:
            return url

    def fetch_content(self, url: str) -> str:
        """
        Fetch content using curl_cffi to bypass potential blocks.
        """
        try:
            from curl_cffi import requests

            # Impersonate Chrome to look like a real browser
            response = requests.get(
                url,
                impersonate="chrome120",
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.text

        except ImportError:
            raise Exception("curl_cffi not installed")
        except Exception as e:
            # Check for specific blocked messages or codes if possible
            if "429" in str(e) or "403" in str(e):
                raise Exception(
                    f"LinkedIn blocked the request ({str(e)}). Try manual mode."
                )
            raise Exception(f"LinkedIn fetch failed: {str(e)}")

    def extract_job_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        # 1. JSON-LD (Best Source)
        try:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    data = json.loads(script.get_text())
                    if isinstance(data, dict) and data.get("@type") == "JobPosting":
                        return {
                            "title": data.get("title", ""),
                            "company": data.get("hiringOrganization", {}).get(
                                "name", ""
                            ),
                            "description": data.get("description", ""),
                            "requirements": [],  # JSON-LD usually has full description but not separate requirements
                            "url": self.normalize_url(url),
                            "source": "LinkedIn",
                        }
                except Exception:
                    continue
        except Exception:
            pass

        # 2. HTML Parsing (Fallback)
        container = self._find_best_container(soup)

        # Description
        description = ""
        if container:
            # Clean artifacts
            for tag in container.find_all(
                ["button", "div.details-pane__content", "section.ad-banner"]
            ):
                tag.decompose()
            description = container.get_text(separator="\n", strip=True)

        return {
            "title": self._extract_title(soup),
            "company": self._extract_company(soup),
            "description": description,
            "requirements": [],  # Requirements extraction is hard on LinkedIn's unstructured text
            "url": self.normalize_url(url),
            "source": "LinkedIn",
        }

    def _find_best_container(self, soup: BeautifulSoup) -> BeautifulSoup:
        # LinkedIn specific selectors
        selectors = [
            ".core-section-container",
            ".job-details-jobs-unified-top-card__content-container",
            ".jobs-description__content",
            "#job-details",
            ".description__text",
        ]

        for selector in selectors:
            candidate = soup.select_one(selector)
            if candidate and len(candidate.get_text(strip=True)) > 100:
                return candidate

        # Fallback to body to avoid crashing, though likely garbage
        return soup.body if soup.body else soup

    def _extract_title(self, soup: BeautifulSoup) -> str:
        selectors = [
            "h1.top-card-layout__title",
            ".job-details-jobs-unified-top-card__job-title",
            "h1.job-title",
            ".jobs-unified-top-card__job-title",
        ]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        # Fallback to title tag
        if soup.title:
            return soup.title.get_text(strip=True).split("|")[0].strip()
        return "Unknown Job"

    def _extract_company(self, soup: BeautifulSoup) -> str:
        selectors = [
            ".topcard__org-name-link",
            ".job-details-jobs-unified-top-card__company-name",
            ".jobs-unified-top-card__company-name",
            "a.topcard__org-name-link",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        return "Unknown Company"
