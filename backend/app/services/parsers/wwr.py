from bs4 import BeautifulSoup
from typing import Dict, Optional
import json
from .base import BaseParser

class WWRParser(BaseParser):
    """Parser for We Work Remotely job pages"""
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize WWR URL.
        Typically: https://weworkremotely.com/remote-jobs/slug
        """
        return url.split("?")[0]

    def fetch_content(self, url: str) -> str:
        """
        Fetch content using curl_cffi to bypass potential blocks.
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
                timeout=30
            )
            response.raise_for_status()
            return response.text
            
        except ImportError:
            raise Exception("curl_cffi not installed")
        except Exception as e:
            raise Exception(f"WWR fetch failed: {str(e)}")

    def extract_job_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract job data from We Work Remotely HTML"""
        
        # 1. Try JSON-LD (Primary)
        # WWR often has unescaped chars, so we need strict=False
        try:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    text = script.get_text()
                    if not text.strip():
                        continue
                        
                    data = json.loads(text, strict=False)
                    
                    if isinstance(data, dict) and data.get("@type") == "JobPosting":
                         description = data.get("description", "")
                         if description:
                             desc_soup = BeautifulSoup(description, "html.parser")
                             description = desc_soup.get_text(separator="\n\n", strip=True)
                             
                         return {
                            "title": data.get("title", "Unknown Job"),
                            "company": data.get("hiringOrganization", {}).get("name", "Unknown Company"),
                            "description": description,
                            "requirements": [],
                            "url": self.normalize_url(url),
                            "source": "WeWorkRemotely"
                         }
                except Exception:
                    continue
        except Exception:
            pass

        # 2. HTML Fallback (Secondary)
        
        # Title & Company (Header Layer)
        header_container = soup.find("div", class_="listing-header-container")
        
        title_text = "Unknown Job"
        company_text = "Unknown Company"
        
        if header_container:
            title_elem = header_container.find("h1")
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                
            company_card = header_container.find("div", class_="company-card")
            if company_card:
                company_elem = company_card.find("h2")
                if company_elem:
                    company_text = company_elem.get_text(strip=True)
        else:
            # Fallback for some old layouts
            h1 = soup.find("h1")
            if h1:
                title_text = h1.get_text(strip=True)

        # Description
        description_div = soup.find("div", id="job-listing-show-container")
        
        desc_text = ""
        if description_div:
            # Clean line breaks
            for br in description_div.find_all("br"):
                br.replace_with("\n")
            
            # Remove the "Apply for this position" button area if it's inside
            apply_btn = description_div.find("div", class_="apply_tooltip")
            if apply_btn:
                apply_btn.decompose()
                
            desc_text = description_div.get_text(separator="\n\n", strip=True)
        
        return {
            "title": title_text,
            "company": company_text,
            "description": desc_text,
            "requirements": [],
            "url": self.normalize_url(url),
            "source": "WeWorkRemotely"
        }
