"""
CV Parser Service — Uses LlamaParse to extract structured data from PDF CVs.
"""
import logging
from typing import Optional
from pydantic import BaseModel
from llama_parse import LlamaParse
from app.core.config import settings
from app.core.logging.prompt_audit import prompt_audit_logger
from pydantic import ValidationError

logger = logging.getLogger("app.services.cv_refresh.cv_parsers.cv_parser_service")


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
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class CVEducation(BaseModel):
    degree: str = ""
    field_of_study: str = ""
    institution: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""


class CVData(BaseModel):
    contact: CVContact = CVContact()
    summary: str = ""
    experiences: list[CVExperience] = []
    education: list[CVEducation] = []
    skills: list[str] = []
    languages: list[str] = []


# ── Extraction prompt ────────────────────────────────────────────────────────

STRUCTURING_PROMPT = """\
You are an expert CV/resume data extractor. Your task is to parse the following CV content
(in markdown format) and return a single JSON object.

IMPORTANT RULES:
1. Extract ALL work experiences and ALL education entries — do not skip any.
2. For experiences, look for section headers like "Work Experience", "Professional Experience",
   "Employment History", "Career History", or similar.
3. For education, look for section headers like "Education", "Academic Background",
   "Qualifications", "Training", or similar.
4. Preserve the original date formats from the CV (e.g. "Jan 2020", "2020-01", "2020").
5. If a field is missing, use an empty string or empty list.
6. For "description" in experiences and education: combine all bullet points into a single multi-line string (e.g. "• Bullet 1\n• Bullet 2").
7. For "summary": use the professional summary/profile/objective section if present, otherwise leave empty.
8. Extract the candidate's core contact information (email, phone, linkedin, address) if present. Make sure to capture the phone number and email correctly.

JSON Schema:
{{
  "contact": {{"name": "", "email": "", "phone": "", "linkedin": "", "address": ""}},
  "summary": "",
  "experiences": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "location": "City, Country",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "description": "• Bullet 1\n• Bullet 2\n• Bullet 3"
    }}
  ],
  "education": [
    {{
      "degree": "MSc / Bachelor / PhD / etc.",
      "field_of_study": "Computer Science",
      "institution": "University Name",
      "start_date": "2016",
      "end_date": "2018",
      "description": "Thesis topic, notable coursework, or achievements"
    }}
  ],
  "skills": ["Python", "React"],
  "languages": ["English", "French"]
}}

CV Content:
---
{cv_markdown}
---

Return ONLY the JSON object. No extra text, no markdown fences, no explanation.
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
        import traceback

        logger.info(f"Parsing CV from: {file_path}")

        # Step 1: Extract markdown from PDF via LlamaParse
        try:
            documents = await self.parser.aload_data(file_path)
        except Exception as e:
            logger.error(f"LlamaParse failed: {e}\n{traceback.format_exc()}")
            raise ValueError(f"LlamaParse extraction failed: {e}")

        if not documents:
            raise ValueError("LlamaParse returned no content for the uploaded PDF.")

        cv_markdown = "\n\n".join(doc.text for doc in documents)
        
        # Inject raw text from first page to ensure headers/footers (contact info) are available
        try:
            import edgeparse
            first_page_text = edgeparse.convert(file_path, format="markdown")
            # Prepend the raw text to the markdown
            cv_markdown = f"--- RAW TEXT (Contains Contact Info) ---\n{first_page_text[:1000]}\n\n--- STRUCTURED MARKDOWN ---\n" + cv_markdown
        except Exception as e:
            logger.warning(f"Could not extract raw text fallback: {e}")
            
        logger.info(f"LlamaParse extracted {len(cv_markdown)} characters of markdown")

        # Step 2: Structure the markdown using the LLM extraction agent
        try:
            cv_data = await self._structure_with_llm(cv_markdown)
            return cv_data
        except Exception as e:
            logger.error(f"Structuring failed after LlamaParse: {e}\n{traceback.format_exc()}")
            # Return raw markdown as summary fallback
            return CVData(summary=cv_markdown[:500])

    async def _structure_with_llm(self, cv_markdown: str) -> CVData:
        """Use Groq LLM to convert markdown → CVData."""
        import json

        prompt = STRUCTURING_PROMPT.format(cv_markdown=cv_markdown[:8000])
        raw = ""

        try:
            from pydantic_ai import Agent
            from pydantic_ai.models.openai import OpenAIChatModel
            from app.services.platform.agents import create_custom_openai_provider

            provider = create_custom_openai_provider(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.GROQ_API_KEY,
            )
            model = OpenAIChatModel(
                model_name=settings.GROQ_MODEL_1,
                provider=provider,
            )
            agent = Agent(
                model,
                system_prompt=(
                    "You are an expert CV data extractor. "
                    "Return ONLY valid JSON matching the requested schema. "
                    "Extract every single work experience and education entry. "
                    "No markdown fences, no extra text, no explanation."
                ),
                model_settings={"temperature": 0.1, "max_tokens": 4000},
            )
            result = await agent.run(prompt)
            raw = result.output if hasattr(result, 'output') else str(result.data)

            logger.info(f"Groq raw output length: {len(raw)} chars")
            logger.debug(f"Groq raw output (first 500): {raw[:500]}")

            # Robust JSON extraction
            cleaned = self._extract_json(raw)
            data = json.loads(cleaned)
            return CVData(**data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON output: {e}\nRaw: {raw[:500]}")
            prompt_audit_logger.log_failure(
                context="CV Parsing (JSON Decode)",
                raw_output=raw,
                error=str(e),
                model_name=settings.GROQ_MODEL_1
            )
            return CVData(summary=cv_markdown[:500])
        except ValidationError as e:
            logger.error(f"Failed to validate LLM output against CVData: {e}\nRaw: {raw[:500]}")
            prompt_audit_logger.log_failure(
                context="CV Parsing (Pydantic Validation)",
                raw_output=raw,
                error=str(e),
                model_name=settings.GROQ_MODEL_1
            )
            return CVData(summary=cv_markdown[:500])
        except Exception as e:
            logger.error(f"LLM structuring failed: {e}")
            return CVData(summary=cv_markdown[:500])

    @staticmethod
    def _extract_json(raw: str) -> str:
        """Extract a JSON object from potentially noisy LLM output."""
        import re

        text = raw.strip()

        # Remove markdown code fences (```json ... ``` or ``` ... ```)
        fence_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
        match = fence_pattern.search(text)
        if match:
            text = match.group(1).strip()

        # Find the first '{' and the last '}' to extract the JSON object
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace : last_brace + 1]

        # Remove trailing commas before closing braces/brackets (common LLM mistake)
        text = re.sub(r",\s*([}\]])", r"\1", text)

        return text


# Module-level singleton
cv_parser_service = CVParserService()
