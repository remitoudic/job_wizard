from typing import Dict, Any
from bs4 import BeautifulSoup
import re
from .base import BaseParser


class GenericParser(BaseParser):
    """Fallback parser for any website"""

    @property
    def should_use_browser(self) -> bool:
        """Whether this parser requires a browser (Playwright) to fetch content"""
        return False

    def normalize_url(self, url: str) -> str:
        return url

    def extract_job_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        raw_description = self._extract_description(soup)
        normalized = self._normalize_description(raw_description)

        return {
            "title": self._extract_title(soup),
            "company": self._extract_company(soup),
            "description": normalized["markdown"],
            "requirements": self._extract_requirements(soup),
            "url": url,
            "source": self._extract_source(soup),
        }

    def _find_best_container(self, soup: BeautifulSoup) -> BeautifulSoup:
        selectors = [
            ".job-description",
            "[data-job-description]",
            "#job-details",
            ".job-view-content",
            "[class*='description']",
        ]

        for selector in selectors:
            candidates = soup.select(selector)
            for candidate in candidates:
                if len(candidate.get_text(strip=True)) > 200:
                    return candidate

        for tag in ["main", "article"]:
            element = soup.find(tag)
            if element and len(element.get_text(strip=True)) > 200:
                return element

        body = soup.find("body")
        return body if body else soup

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title = "Job Position"

        # Structured Data
        sd = self._extract_structured_data(soup)
        if sd.get("title"):
            title = sd["title"].strip()
        else:
            # OG
            og = soup.find("meta", property="og:title")
            if og and og.get("content"):
                title = og.get("content").strip()
            else:
                # Common selectors
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
                        title = element.get_text(strip=True)
                        break
                else:
                    # Fallback
                    title_tag = soup.find("title")
                    if title_tag:
                        title = title_tag.get_text(strip=True).split("|")[0].strip()

        return self._clean_title(title)

    def _extract_company(self, soup: BeautifulSoup) -> str:
        # Structured data
        sd = self._extract_structured_data(soup)
        if sd.get("hiringOrganization"):
            org = sd.get("hiringOrganization")
            if isinstance(org, dict) and org.get("name"):
                return org.get("name").strip()
            if isinstance(org, str):
                return org.strip()

        # OG
        og = soup.find("meta", property="og:site_name") or soup.find(
            "meta", property="og:publisher"
        )
        if og and og.get("content"):
            return og.get("content").strip()

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

        # Title fallback
        title_tag = soup.find("title")
        if title_tag:
            parts = title_tag.get_text().split("|")
            if len(parts) > 1:
                return parts[1].strip()

        return "Company"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        # Structured data
        sd = self._extract_structured_data(soup)
        if sd.get("description"):
            desc = sd.get("description")
            if isinstance(desc, str) and desc.strip():
                return re.sub(r"\n\s*\n", "\n\n", desc.strip())

        container = self._find_best_container(soup)

        # Cleanup
        for tag in container.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = container.get_text(separator="\n", strip=True)
        text = re.sub(r"\n\s*\n", "\n\n", text)

        if len(text) > 100:
            return text

        # Fallback to meta
        og = soup.find("meta", property="og:description") or soup.find(
            "meta", attrs={"name": "description"}
        )
        if og and og.get("content"):
            return og.get("content").strip()

        # Last resort
        paragraphs = soup.find_all("p")
        valid_paragraphs = [
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 20
        ]
        text = "\n\n".join(valid_paragraphs)
        return text if text else "No description available"

    def _extract_requirements(self, soup: BeautifulSoup) -> list[str]:
        requirements = []
        container = self._find_best_container(soup)
        lists = container.find_all(["ul", "ol"])

        for lst in lists:
            items = lst.find_all("li")
            for item in items:
                text = item.get_text(strip=True)
                if text and 10 < len(text) < 300:
                    if not any(
                        x in text.lower()
                        for x in ["copyright", "privacy policy", "terms", "cookies"]
                    ):
                        requirements.append(text)

        if not requirements:
            description = self._extract_description(soup)
            lines = description.split("\n")
            for line in lines:
                line = line.strip()
                if line and (
                    line.startswith("•")
                    or line.startswith("-")
                    or re.match(r"^\d+\.", line)
                ):
                    cleaned = line.lstrip("•-0123456789. ")
                    if len(cleaned) > 10:
                        requirements.append(cleaned)

        return requirements[:15]

    def _extract_source(self, soup: BeautifulSoup) -> str | None:
        title_tag = soup.find("title")
        if title_tag:
            text = title_tag.get_text(strip=True)
            if "|" in text:
                return text.split("|")[-1].strip()
            if " - " in text:
                return text.split(" - ")[-1].strip()

        og = soup.find("meta", property="og:site_name")
        if og and og.get("content"):
            return og.get("content").strip()

        return None

    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict:
        data: Dict = {}
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            try:
                import json

                payload = json.loads(s.string or "{}")
                if isinstance(payload, list):
                    for item in payload:
                        if isinstance(item, dict) and item.get("@type") in (
                            "JobPosting",
                            "JobPostingSpecification",
                        ):
                            payload = item
                            break
                if isinstance(payload, dict):
                    t = payload.get("@type") or payload.get("type")
                    if t and ("JobPosting" in t or t == "JobPosting"):
                        if payload.get("title"):
                            data["title"] = payload.get("title")
                        if payload.get("description"):
                            data["description"] = payload.get("description")
                        if payload.get("hiringOrganization"):
                            data["hiringOrganization"] = payload.get(
                                "hiringOrganization"
                            )
                        return data
            except Exception:
                continue
        return data
