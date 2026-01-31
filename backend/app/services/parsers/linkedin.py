from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from .generic import GenericParser

class LinkedInParser(GenericParser):
    """Specialized parser for LinkedIn"""

    def normalize_url(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            # Check for currentJobId param
            query = parse_qs(parsed.query)
            job_id = query.get("currentJobId")
            
            if job_id and job_id[0]:
                return f"https://www.linkedin.com/jobs/view/{job_id[0]}/"
            
            return url
        except Exception:
            return url

    def _find_best_container(self, soup: BeautifulSoup) -> BeautifulSoup:
        # LinkedIn specific selectors
        selectors = [
            ".core-section-container",
            ".job-details-jobs-unified-top-card__content-container",
            ".jobs-description__content",
        ]
        
        for selector in selectors:
            candidate = soup.select_one(selector)
            if candidate and len(candidate.get_text(strip=True)) > 200:
                return candidate
                
        # Fallback to generic strategy
        return super()._find_best_container(soup)

    def _extract_company(self, soup: BeautifulSoup) -> str:
        selectors = [
            ".topcard__org-name-link",
            ".job-details-jobs-unified-top-card__company-name",
            ".jobs-unified-top-card__company-name"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
                
        return super()._extract_company(soup)
