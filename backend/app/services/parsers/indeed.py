import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from .generic import GenericParser

class IndeedParser(GenericParser):
    """Specialized parser for Indeed.com"""

    @property
    def should_use_browser(self) -> bool:
        return False
        # return True

    def normalize_url(self, url: str) -> str:
        """
        Converts Indeed search URLs to canonical job URLs.
        Preserves the country subdomain (e.g. de.indeed.com).
        """
        # Deactivate automatic parsing for Indeed
        raise Exception("Indeed does not allow automatic extracting of job descriptions. Please manually paste the job description content.")

        # Original logic retained for future implementation
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc or "www.indeed.com"
            
            # Try vjk parameter (often in search results)
            vjk_match = re.search(r"[?&]vjk=([a-zA-Z0-9]+)", url)
            if vjk_match:
                jk = vjk_match.group(1)
                return f"https://{domain}/viewjob?jk={jk}"

            # Try jk parameter
            jk_match = re.search(r"[?&]jk=([a-zA-Z0-9]+)", url)
            if jk_match:
                return f"https://{domain}/viewjob?jk={jk_match.group(1)}"
            
            return url
        except Exception:
            return url

    def _find_best_container(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Indeed job content is usually in #jobDescriptionText"""
        job_description = soup.select_one("#jobDescriptionText")
        if job_description and len(job_description.get_text(strip=True)) > 200:
            return job_description
            
        # Fallback to generic strategy if selector fails or content is too short
        return super()._find_best_container(soup)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Indeed specific title extraction"""
        # Indeed often has title in h1 with jobsearch-JobInfoHeader-title class
        header_title = soup.select_one("h1[class*='JobInfoHeader-title']")
        if header_title:
            return self._clean_title(header_title.get_text(strip=True))
            
        return super()._extract_title(soup)

    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Indeed specific company extraction"""
        # Indeed company link/text often in undernourished sub-headers
        company_elem = soup.select_one("[data-company-name='true']") or soup.select_one(".jobsearch-InlineCompanyRating div")
        if company_elem:
            return company_elem.get_text(strip=True)
            
        return super()._extract_company(soup)
