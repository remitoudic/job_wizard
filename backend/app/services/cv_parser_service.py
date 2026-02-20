"""
CV Parser Service — Uses LlamaParse to extract structured data from PDF CVs.
"""
import logging
from typing import Optional
from pydantic import BaseModel
from llama_parse import LlamaParse
from app.core.config import settings

logger = logging.getLogger("app.services.cv_parser_service")


# ── Pydantic models for structured CV data ──────────────────────────────────

class CVContact(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    address: str = ""


class CVExperience(BaseModel):
    title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class CVEducation(BaseModel):
    degree: str = ""
    institution: str = ""
    start_date: str = ""
    end_date: str = ""


class CVData(BaseModel):
    contact: CVContact = CVContact()
    summary: str = ""
    experiences: list[CVExperience] = []
    education: list[CVEducation] = []
    skills: list[str] = []
    languages: list[str] = []


# ── Extraction prompt ────────────────────────────────────────────────────────

STRUCTURING_PROMPT = """\
You are a CV data extractor. Given the following CV content in markdown format,
extract the structured data as a JSON object matching this exact schema.
If a field is not present, use an empty string or empty list as appropriate.

Schema:
{
  "contact": {"name": "", "email": "", "phone": "", "linkedin": "", "address": ""},
  "summary": "",
  "experiences": [{"title": "", "company": "", "start_date": "", "end_date": "", "description": ""}],
  "education": [{"degree": "", "institution": "", "start_date": "", "end_date": ""}],
  "skills": [],
  "languages": []
}

CV Content:
---
{cv_markdown}
---

Return ONLY the JSON object. No extra text, no markdown fences.
"""


class CVParserService:
    """Parse a PDF CV using LlamaParse and structure the results."""

    def __init__(self):
        self._parser: Optional[LlamaParse] = None

    @property
    def parser(self) -> LlamaParse:
        if self._parser is None:
            if not settings.LLAMA_CLOUD_API_KEY:
                raise RuntimeError(
                    "LLAMA_CLOUD_API_KEY is not set. "
                    "Please add it to your .env file."
                )
            self._parser = LlamaParse(
                api_key=settings.LLAMA_CLOUD_API_KEY,
                result_type="markdown",
                verbose=False,
            )
        return self._parser

    async def parse_pdf(self, file_path: str) -> CVData:
        """
        Parse a PDF CV file and return structured CVData.

        1. Send the PDF to LlamaParse → get markdown.
        2. Use a simple JSON-extraction prompt to structure the markdown.
        """
        import json

        logger.info(f"Parsing CV from: {file_path}")

        # Step 1: Extract markdown from PDF via LlamaParse
        documents = await self.parser.aload_data(file_path)
        if not documents:
            raise ValueError("LlamaParse returned no content for the uploaded PDF.")

        cv_markdown = "\n\n".join(doc.text for doc in documents)
        logger.info(f"LlamaParse extracted {len(cv_markdown)} characters of markdown")

        # Step 2: Structure the markdown using the LLM extraction agent
        cv_data = await self._structure_with_llm(cv_markdown)
        return cv_data

    async def _structure_with_llm(self, cv_markdown: str) -> CVData:
        """Use the existing extraction agent to convert markdown → CVData."""
        import json

        prompt = STRUCTURING_PROMPT.format(cv_markdown=cv_markdown[:8000])

        try:
            from app.services.agents import create_extraction_agent
            from app.services.llm_provider_service import llm_provider_service

            # Try remote model first for better quality
            provider_config = llm_provider_service.get_provider_config()
            if provider_config and provider_config.get("api_key"):
                from pydantic_ai import Agent
                agent = Agent(
                    f"{provider_config['provider_prefix']}{provider_config['model_1']}",
                    system_prompt="You are a JSON data extractor. Return only valid JSON.",
                )
                result = await agent.run(prompt)
                raw = result.output if hasattr(result, 'output') else str(result.data)
            else:
                # Fallback to local Ollama
                from pydantic_ai import Agent
                agent = Agent(
                    f"ollama:{settings.OLLAMA_MODEL}",
                    system_prompt="You are a JSON data extractor. Return only valid JSON.",
                )
                result = await agent.run(prompt)
                raw = result.output if hasattr(result, 'output') else str(result.data)

            # Clean and parse JSON
            raw = raw.strip()
            if raw.startswith("```"):
                # Remove markdown code fences
                lines = raw.split("\n")
                raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                raw = raw.strip()

            data = json.loads(raw)
            return CVData(**data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON output: {e}\nRaw: {raw[:500]}")
            # Return a minimal CVData with what we have
            return CVData(summary=cv_markdown[:500])
        except Exception as e:
            logger.error(f"LLM structuring failed: {e}")
            # Graceful fallback: return unstructured summary
            return CVData(summary=cv_markdown[:500])


# Module-level singleton
cv_parser_service = CVParserService()
