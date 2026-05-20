from typing import Dict, Type
from urllib.parse import urlparse
from .base import BaseParser
from .generic import GenericParser
from .linkedin import LinkedInParser

from .indeed import IndeedParser
from .stepstone import StepStoneParser
from .arbeitnow import ArbeitnowParser
from .wwr import WWRParser


class ParserRegistry:
    """Registry to manage and retrieve job parsers"""

    _parsers: Dict[str, Type[BaseParser]] = {
        "linkedin.com": LinkedInParser,
        "www.linkedin.com": LinkedInParser,
        "indeed.com": IndeedParser,
        "www.indeed.com": IndeedParser,
        "de.indeed.com": IndeedParser,
        "stepstone.de": StepStoneParser,
        "www.stepstone.de": StepStoneParser,
        "arbeitnow.com": ArbeitnowParser,
        "www.arbeitnow.com": ArbeitnowParser,
        "weworkremotely.com": WWRParser,
        "www.weworkremotely.com": WWRParser,
    }

    @classmethod
    def get_parser(cls, url: str) -> BaseParser:
        """Get the appropriate parser instance for the URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            parser_class = cls._parsers.get(domain)
            if parser_class:
                return parser_class()

            # Try partial match if no exact match
            for registered_domain, p_class in cls._parsers.items():
                if registered_domain in domain:
                    return p_class()

        except Exception:
            pass

        return GenericParser()
