"""
CrewAI Cover Letter Generation Workflow
=======================================

This module defines the 3-step sequential AI agent workflow for generating cover letters.
It leverages CrewAI to simulate an "agency" process containing:
1. Profile Analyst (Strategic data extraction)
2. Copywriter (Drafting the narrative)
3. Editor (Polishing and formatting)

By separating these tasks, we significantly reduce LLM "hallucinations" and create
much higher quality cover letters than a single-prompt approach.
"""

import json
import logging
from typing import Optional
import httpx

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from app.services.platform.llm_provider_service import llm_provider_service
from app.core.config import settings

logger = logging.getLogger(__name__)

# ==============================================================================
# Provider Compatibility Hooks
# ==============================================================================
# Some remote LLM providers (like Groq) inject custom fields into their OpenAI-compatible
# API responses. Langchain strict-parses these responses.
# The hooks below strip out these extra fields (e.g. `service_tier`) before Langchain sees them.


async def strip_service_tier_hook_async(response: httpx.Response):
    """Async hook to strip 'service_tier' from Groq responses."""
    if response.status_code == 200:
        try:
            await response.aread()
            if b"service_tier" in response.content:
                data = response.json()
                if "service_tier" in data:
                    del data["service_tier"]
                    response._content = json.dumps(data).encode("utf-8")
        except Exception:
            pass


def strip_service_tier_hook_sync(response: httpx.Response):
    """Sync hook to strip 'service_tier' from Groq responses."""
    if response.status_code == 200:
        try:
            response.read()
            if b"service_tier" in response.content:
                data = response.json()
                if "service_tier" in data:
                    del data["service_tier"]
                    response._content = json.dumps(data).encode("utf-8")
        except Exception:
            pass


# ==============================================================================
# LLM Initialization
# ==============================================================================


def get_candidate_configs() -> list[dict]:
    """
    Returns an ordered list of candidate provider configs for CrewAI.
    Priority:
    1. OpenRouter primary (nvidia/nemotron-3.5-lightning:free)
    2. OpenRouter fallback (nvidia/nemotron-3-super-120b-a12b:free)
    3. Groq (qwen/qwen3.8-27b - fast, high TPM limits)
    4. Groq secondary (openai/gpt-oss-120b)
    """
    candidates = []

    # 1. OpenRouter (preferred primary for CrewAI)
    if settings.OPENROUTER_API_KEY:
        candidates.append(
            {
                "name": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": settings.OPENROUTER_API_KEY,
                "model_1": settings.OPENROUTER_MODEL,
            }
        )
        if (
            settings.OPENROUTER_MODEL_2
            and settings.OPENROUTER_MODEL_2 != settings.OPENROUTER_MODEL
        ):
            candidates.append(
                {
                    "name": "openrouter",
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key": settings.OPENROUTER_API_KEY,
                    "model_1": settings.OPENROUTER_MODEL_2,
                }
            )

    # 2. Active provider from service
    try:
        active_cfg = llm_provider_service.get_provider_config()
        if active_cfg:
            candidates.append(active_cfg)
    except Exception as e:
        logger.warning(f"Failed to fetch active provider config: {e}")

    # 3. Groq fallbacks with verified models (Prioritize Qwen for speed and high TPM)
    if settings.GROQ_API_KEY:
        candidates.append(
            {
                "name": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.GROQ_API_KEY,
                "model_1": settings.GROQ_MODEL_2,
            }
        )
        candidates.append(
            {
                "name": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.GROQ_API_KEY,
                "model_1": settings.GROQ_MODEL_1,
            }
        )

    # Deduplicate while preserving order based on (name, model_1)
    unique_candidates = []
    seen = set()
    for c in candidates:
        key = (c.get("name"), c.get("model_1"))
        if key not in seen and c.get("model_1"):
            seen.add(key)
            unique_candidates.append(c)

    return (
        unique_candidates
        if unique_candidates
        else [
            {
                "name": "groq",
                "model_1": "qwen/qwen3.8-27b",
                "api_key": "dummy-key",
            }
        ]
    )


def get_llm_for_agent(temperature: float, config: Optional[dict] = None) -> ChatOpenAI:
    """
    Constructs the LangChain LLM instance dynamically.

    Why dynamic?
    Instead of hardcoding OpenAI, we fetch the provider config (OpenRouter, Groq, etc.)
    with automatic failover support if an upstream provider hits rate limits or 404s.

    Args:
        temperature (float): The creativity setting. 0.1 for analytical, 0.7 for creative.
        config (Optional[dict]): Specific provider config to use. If None, uses active provider.
    """
    if config is None:
        config = llm_provider_service.get_provider_config()

    # Grab the model defined in the candidate config
    model_name = config.get("model_1", "openai/gpt-oss-120b")

    # LangChain ChatOpenAI requires a non-empty api_key during instantiation.
    api_key = config.get("api_key")
    if not api_key:
        api_key = "dummy-key"

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        openai_api_key=api_key,  # For backward compatibility with older LangChain/Pydantic validation
        base_url=config.get("base_url"),
        temperature=temperature,
    )


# ==============================================================================
# Core Workflow Execution
# ==============================================================================


def run_crewai_generation(
    job_description: str,
    job_title: str,
    company: str,
    requirements: list[str],
    user_name: str = "",
    user_skills: str = "",
    context_text: Optional[str] = None,
    language: str = "english",
    custom_instructions: Optional[str] = None,
) -> str:
    """
    Kicks off the Sequential CrewAI process to generate a cover letter.

    Iterates through candidate model providers with automatic failover
    to ensure resilient generation even under rate limits or model deprecations.
    """
    logger.info(f"Starting CrewAI generation for {company} - {job_title}")

    req_list = ", ".join(requirements) if requirements else "See description"
    candidates = get_candidate_configs()
    last_error = None

    lang_lower = (language or "english").lower()
    if lang_lower == "german":
        salutation_hint = "Sehr geehrte Damen und Herren,"
    elif lang_lower == "french":
        salutation_hint = "Madame, Monsieur,"
    elif lang_lower == "spanish":
        salutation_hint = "Estimado/a Responsable de Selección,"
    else:
        salutation_hint = (
            f"Dear Hiring Manager at {company}," if company else "Dear Hiring Manager,"
        )

    for candidate_config in candidates:
        provider_name = candidate_config.get("name", "unknown")
        model_name = candidate_config.get("model_1", "unknown")
        logger.info(
            f"Attempting CrewAI generation with candidate: {provider_name} ({model_name})"
        )

        try:
            # ---------------------------------------------------------
            # AGENT 1: The Profile Analyst
            # Temperature: 0.1 (Very low creativity, high precision)
            # Goal: Extract raw facts. Prevents the final letter from making things up.
            # ---------------------------------------------------------
            analyst = Agent(
                role="Profile Analyst",
                goal="Cross-reference the candidate's profile with the Job Description to find the 3 strongest overlaps.",
                backstory="A ruthless tech recruiter who knows exactly what hiring managers look for. You only care about cold, hard facts and perfect alignment between a candidate's history and the job's needs.",
                verbose=True,
                allow_delegation=False,
                llm=get_llm_for_agent(temperature=0.1, config=candidate_config),
            )

            # ---------------------------------------------------------
            # AGENT 2: The Copywriter
            # Temperature: 0.7 (High creativity, persuasive)
            # Goal: Take the Analyst's dry facts and turn them into a compelling story.
            # ---------------------------------------------------------
            copywriter = Agent(
                role="Expert Career Coach & Copywriter",
                goal="Turn the Analyst's brief into a cohesive, persuasive cover letter narrative.",
                backstory="An expert career coach and persuasive storyteller who writes engaging, human copy. You focus on enthusiasm and showing how the candidate's past results will solve the hiring company's future problems.",
                verbose=True,
                allow_delegation=False,
                llm=get_llm_for_agent(temperature=0.7, config=candidate_config),
            )

            # ---------------------------------------------------------
            # AGENT 3: The Editor
            # Temperature: 0.3 (Low creativity, strict formatting)
            # Goal: Final polish, remove AI cliches, enforce word counts.
            # ---------------------------------------------------------
            editor = Agent(
                role="Strict Copy Editor",
                goal="Refine the cover letter, cut fluff, and ensure perfect formatting.",
                backstory="A strict copy editor who hates fluff, buzzwords, and overly formal corporate speak. You cut common AI clichés ('In today's fast-paced world', 'delve', 'testament to'), tighten prose, and format perfectly.",
                verbose=True,
                allow_delegation=False,
                llm=get_llm_for_agent(temperature=0.3, config=candidate_config),
            )

            # ---------------------------------------------------------
            # TASK DEFINITIONS
            # ---------------------------------------------------------

            # Task 1: Strategy (Handled by Analyst)
            strategy_task = Task(
                description=f"""
                Analyze the candidate's history and the job requirements. DO NOT write a letter.
                Output a structured brief containing:
                1. The candidate's 3 most relevant achievements for this specific role.
                2. A suggested 'hook' or opening angle based on their background.
                3. Any missing skills the copywriter should downplay or pivot away from.

                Job Title: {job_title}
                Company: {company}
                Job Requirements: {req_list}
                Job Description: {job_description}
                Candidate Skills: {user_skills}
                Candidate Background: {context_text or "No detailed background provided."}
                Custom Guidance: {custom_instructions if custom_instructions else "None provided."}
                """,
                expected_output="A structured brief detailing the 3 strongest overlaps, a hook, and skills to downplay.",
                agent=analyst,
            )

            # Task 2: Drafting (Handled by Copywriter)
            drafting_task = Task(
                description=f"""
                Write the first draft of the cover letter based ONLY on the points provided in the Analyst's brief.
                CRITICAL INSTRUCTIONS:
                1. OUTPUT BODY ONLY. Do NOT include a header, date, applicant contact info, or recipient address block at the top.
                2. Start directly with the salutation: {salutation_hint}
                3. Do NOT include a signature or sign-off (e.g. 'Sincerely, [Name]'). The template engine handles this.
                4. Do NOT include placeholders like '[Your Name]' or '[Date]'.
                5. Keep between 200 and 350 words in a confident, professional, yet approachable tone.
                6. The letter MUST be written in {language}.
                7. Adhere to any Custom Guidance: {custom_instructions if custom_instructions else "None"}

                Target Company: {company}
                Target Role: {job_title}
                """,
                expected_output="A clean body draft of the cover letter starting with the salutation.",
                agent=copywriter,
            )

            # Task 3: Polish (Handled by Editor)
            polish_task = Task(
                description=f"""
                Review the draft cover letter from the copywriter.
                1. Strip out any hallucinated skills not in the original brief.
                2. Remove sycophantic language or obvious AI tells ('delve', 'testament to', 'thrilled to apply').
                3. Ensure the letter is under 350 words.
                4. STRICTLY OUTPUT BODY ONLY: Ensure it starts directly with '{salutation_hint}' and ends with the concluding sentence of the body.
                5. Remove ANY address block, date, header, 'Sincerely, ...', closing sign-off, or candidate name.
                6. Ensure the final language is {language}.
                7. Do NOT output anything other than the final cover letter body text.
                """,
                expected_output="The final, polished cover letter body text starting with the salutation.",
                agent=editor,
            )

            # ---------------------------------------------------------
            # CREW ASSEMBLY & EXECUTION
            # ---------------------------------------------------------

            cover_letter_crew = Crew(
                agents=[analyst, copywriter, editor],
                tasks=[strategy_task, drafting_task, polish_task],
                process=Process.sequential,  # Tasks execute in exact order
                verbose=True,
            )

            result = cover_letter_crew.kickoff()
            result_str = str(result)
            try:
                from app.services.cover_letter.llm_service import LLMService

                result_str = LLMService.clean_model_output(result_str)
            except Exception as clean_err:
                logger.warning(
                    f"Could not apply clean_model_output to CrewAI output: {clean_err}"
                )

            logger.info(
                f"CrewAI generation completed successfully using {provider_name} ({model_name})."
            )
            return result_str

        except Exception as e:
            last_error = e
            logger.warning(
                f"CrewAI generation failed with {provider_name} ({model_name}): {e}. "
                "Attempting fallback candidate..."
            )
            continue

    logger.error("All CrewAI generation candidates failed.")
    raise last_error or RuntimeError("CrewAI generation failed across all candidates")
