from abc import ABC, abstractmethod
from typing import Dict, Any
from bs4 import BeautifulSoup
import re
from app.services.job_description_normalizer import normalize_job_post

class BaseParser(ABC):
    """Abstract base class for job parsers"""

    def __init__(self):
        pass

    @abstractmethod
    def normalize_url(self, url: str) -> str:
        """Normalize URL to canonical version"""
        pass

    @abstractmethod
    def extract_job_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract job data from parsed HTML soup"""
        pass

    def _normalize_description(self, raw_description: str) -> Dict[str, str]:
        """Helper to use the shared normalizer"""
        return normalize_job_post(raw_description)

    def _clean_title(self, title: str) -> str:
        """Shared title cleaning logic"""
        # 1. Remove source suffix (anything after |)
        if "|" in title:
            title = title.split("|")[0].strip()
            
        # 2. Regex to match (m/f/d) etc.
        cleaned = re.sub(r'\s*\(?\s*[mwfdx]\s*[|/]\s*[mwfdx]\s*[|/]\s*[mwfdx]\s*\)?', '', title, flags=re.IGNORECASE)
        
        return cleaned.strip()
