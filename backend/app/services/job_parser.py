import httpx
from bs4 import BeautifulSoup
from typing import Dict, List
import re


class JobParser:
    """Service for parsing job descriptions from URLs"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    async def parse_url(self, url: str) -> Dict:
        """
        Parse job description from URL
        
        Args:
            url: Job posting URL
            
        Returns:
            Dictionary with job details
        """
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
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract job title from page"""
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
        selectors = [
            ".company-name",
            ".companyName",
            "[class*='company']",
            "[data-company]",
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
        # Try to find job description container
        selectors = [
            ".job-description",
            ".description",
            "[class*='job-description']",
            "[class*='description']",
            "article",
            "main",
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Get text and clean it
                text = element.get_text(separator="\n", strip=True)
                # Remove excessive whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                if len(text) > 100:  # Ensure we got substantial content
                    return text
        
        # Fallback: get all paragraph text
        paragraphs = soup.find_all("p")
        text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        
        return text if text else "No description available"
    
    def _extract_requirements(self, soup: BeautifulSoup) -> List[str]:
        """Extract job requirements as a list"""
        requirements = []
        
        # Look for lists in the description
        lists = soup.find_all(["ul", "ol"])
        
        for lst in lists:
            items = lst.find_all("li")
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short items
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
                    requirements.append(line.lstrip("•-0123456789. "))
        
        return requirements[:10]  # Limit to top 10 requirements
