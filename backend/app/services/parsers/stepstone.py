from bs4 import BeautifulSoup
from typing import Dict, Optional
import urllib.parse
from .base import BaseParser

class StepStoneParser(BaseParser):
    """Parser for Stepstone job pages"""
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize Stepstone URL to remove tracking parameters.
        Stepstone URLs typically end with an ID or -inline.html
        """
        # Split by ? to remove query parameters
        base_url = url.split("?")[0]
        return base_url

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract job data from JSON-LD structured data"""
        import json
        
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.get_text())
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
        """Extract job data from Method Stepstone HTML"""
        
        # Try JSON-LD first (Most reliable)
        json_ld_data = self._extract_json_ld(soup)
        
        if json_ld_data:
            # Extract fields from JSON-LD
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
                "source": "StepStone"
            }

        # Fallback to scraping (Old method)
        
        # 1. Title extraction
        # Try specific data attributes first, then fallbacks
        title = None
        title_selectors = [
            '[data-at="header-job-title"]',
            '[data-test="detail-header-title"]',
            'h1.listing-job-title',
            'h1'
        ]
        
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(separator=" ", strip=True)
                break
                
        if not title:
             # Fallback to title tag but clean it
             title_tag = soup.find("title")
             if title_tag:
                 title = title_tag.get_text().split("|")[0].strip()

        # 2. Company extraction
        company = "Unknown Company"
        company_selectors = [
            '[data-at="header-company-name"]',
            '[data-test="detail-header-company-name"]',
            'a.listing-content-provider-1',
            '.listing-org-name'
        ]
        
        for selector in company_selectors:
            elem = soup.select_one(selector)
            if elem:
                company = elem.get_text(separator=" ", strip=True)
                break

        # 3. Description extraction
        # Stepstone often wraps content in a specific container
        description = ""
        desc_selectors = [
            '[data-at="job-content"]',
            '.js-app-ld-ContentBlock',
            '.listing-content',
            'div.job-ad-container'
        ]
        
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                # Get text with better formatting
                # Replace <br> with newline
                for br in elem.find_all("br"):
                    br.replace_with("\n")
                
                # Get text
                description = elem.get_text(separator="\n\n", strip=True)
                break
                
        if not description:
            # Fallback: grab all paragraph text if we can't find the main container
            # This is risky but better than nothing
            paragraphs = soup.find_all("p")
            description = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])

        return {
            "title": title or "Unknown Job",
            "company": company,
            "description": description,
            "requirements": [], # Difficult to extract reliably without specific structure
            "url": self.normalize_url(url),
            "source": "StepStone"
        }
