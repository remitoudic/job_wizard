from bs4 import BeautifulSoup
from typing import Dict, Optional
import json
from .base import BaseParser


class ArbeitnowParser(BaseParser):
    """Parser for Arbeitnow job pages"""

    def normalize_url(self, url: str) -> str:
        """
        Normalize Arbeitnow URL.
        Typically: https://www.arbeitnow.com/jobs/slug
        """
        return url.split("?")[0]

    def fetch_content(self, url: str) -> str:
        """
        Fetch content using curl_cffi as requested.
        """
        try:
            from curl_cffi import requests

            # Impersonate Chrome
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
            raise Exception(f"Arbeitnow fetch failed: {str(e)}")

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract job data from JSON-LD structured data"""
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                text = script.get_text()
                if not text.strip():
                    continue

                data = json.loads(text)

                # JSON-LD can be a list or a single object
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "JobPosting":
                            return item
                elif isinstance(data, dict):
                    if data.get("@type") == "JobPosting":
                        return data
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    def extract_job_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract job data from Arbeitnow HTML"""

        # 1. Try JSON-LD (Primary Strategy)
        json_ld_data = self._extract_json_ld(soup)

        if json_ld_data:
            title = json_ld_data.get("title")

            company_data = json_ld_data.get("hiringOrganization", {})
            if isinstance(company_data, dict):
                company = company_data.get("name")
            else:
                company = str(company_data)

            description = json_ld_data.get("description", "")

            # Clean up the description if it contains HTML
            if description:
                # Reuse BeautifulSoup to clean HTML in description
                desc_soup = BeautifulSoup(description, "html.parser")
                description = desc_soup.get_text(separator="\n\n", strip=True)

            return {
                "title": title or "Unknown Job",
                "company": company or "Unknown Company",
                "description": description,
                "requirements": [],
                "url": self.normalize_url(url),
                "source": "Arbeitnow",
            }

        # 2. Fallback: CSS Selectors (Simple backup)
        title = soup.select_one("h1")
        title_text = title.get_text(strip=True) if title else "Unknown Job"

        company = soup.select_one('[itemprop="hiringOrganization"]')
        company_text = company.get_text(strip=True) if company else "Unknown Company"

        # Arbeitnow uses itemprop="description" typically
        description = soup.select_one('[itemprop="description"]')
        if not description:
            description = soup.select_one(".job-description")

        desc_text = ""
        if description:
            # Clean line breaks
            for br in description.find_all("br"):
                br.replace_with("\n")
            desc_text = description.get_text(separator="\n\n", strip=True)

        return {
            "title": title_text,
            "company": company_text,
            "description": desc_text,
            "requirements": [],
            "url": self.normalize_url(url),
            "source": "Arbeitnow",
        }
