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
    1. Groq primary (openai/gpt-oss-120b - fastest 3-agent sequential execution ~8s)
    2. Groq secondary (qwen/qwen3.8-27b - fast, high TPM limits)
    3. Active provider from service
    4. OpenRouter primary (nvidia/nemotron-3-ultra-550b-a55b:free)
    5. OpenRouter fallback (nvidia/nemotron-3.5-lightning:free)
    """
    candidates = []

    # 1. Groq primary & secondary (Fastest inference for 3-agent sequential CrewAI chain)
    if settings.GROQ_API_KEY:
        candidates.append(
            {
                "name": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.GROQ_API_KEY,
                "model_1": settings.GROQ_MODEL_1,
            }
        )
        if settings.GROQ_MODEL_2 and settings.GROQ_MODEL_2 != settings.GROQ_MODEL_1:
            candidates.append(
                {
                    "name": "groq",
                    "base_url": "https://api.groq.com/openai/v1",
                    "api_key": settings.GROQ_API_KEY,
                    "model_1": settings.GROQ_MODEL_2,
                }
            )

    # 2. Active provider from service
    try:
        active_cfg = llm_provider_service.get_provider_config()
        if active_cfg:
            candidates.append(active_cfg)
    except Exception as e:
        logger.warning(f"Failed to fetch active provider config: {e}")

    # 3. NVIDIA NIM candidate (if API key configured and not disabled)
    try:
        nvidia_cfg = llm_provider_service.get_nvidia_config()
        if nvidia_cfg and nvidia_cfg.get("model_1"):
            candidates.append(
                {
                    "name": "nvidia",
                    "base_url": nvidia_cfg["base_url"],
                    "api_key": nvidia_cfg["api_key"],
                    "model_1": nvidia_cfg["model_1"],
                }
            )
    except Exception as e:
        logger.warning(f"Failed to fetch NVIDIA provider config: {e}")

    # 4. OpenRouter fallbacks
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
        lang_style_guide = (
            "Write in natural, idiomatic formal German (Sie-Form) following modern German "
            "Bewerbungsschreiben standards: confident, concrete, and free of stiff translations from English. "
            "End the final body paragraph with a natural German call to action (e.g. 'Über die Gelegenheit, "
            "mich in einem persönlichen Gespräch vorzustellen, freue ich mich sehr.')."
        )
    elif lang_lower == "french":
        salutation_hint = "Madame, Monsieur,"
        lang_style_guide = (
            "Write in natural, idiomatic formal French (vouvoiement) following the classic 'Vous, Moi, Nous' "
            "Lettre de Motivation flow: connect the company's challenges, the candidate's concrete achievements, "
            "and the shared value of collaborating, ending with a polite, confident French closing sentence."
        )
    elif lang_lower == "spanish":
        salutation_hint = "Estimado/a Responsable de Selección,"
        lang_style_guide = (
            "Write in natural, idiomatic formal Spanish (Carta de Presentación standard), "
            "using fluent professional prose and ending with a courteous invitation for an interview."
        )
    else:
        salutation_hint = (
            f"Dear Hiring Manager at {company}," if company else "Dear Hiring Manager,"
        )
        lang_style_guide = "Write in crisp, natural British English with an authentic, executive human voice."

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
            # Goal: Extract verifiable career proof with exact employer names & metrics.
            # ---------------------------------------------------------
            analyst = Agent(
                role="Principal Executive Talent Strategist",
                goal=(
                    "Build a high-signal Evidence & Narrative Dossier mapping the candidate's "
                    "real career achievements (with exact employer names, systems, and metrics) "
                    "to the core challenges of the target role."
                ),
                backstory=(
                    "An elite executive recruiter and technical talent strategist. You despise generic "
                    "claims and anonymized summaries. You mine a candidate's CV for specific company names, "
                    "architectural decisions, quantified outcomes, and domain impact, then organize them into "
                    "two cohesive narrative themes that prove the candidate can solve the hiring team's hardest problems."
                ),
                verbose=True,
                allow_delegation=False,
                llm=get_llm_for_agent(temperature=0.1, config=candidate_config),
            )

            # ---------------------------------------------------------
            # AGENT 2: The Copywriter
            # Temperature: 0.7 (High creativity, persuasive storytelling)
            # Goal: Write a cohesive, human-sounding 4-paragraph executive cover letter.
            # ---------------------------------------------------------
            copywriter = Agent(
                role="Senior Executive Narrative Copywriter",
                goal=(
                    "Craft a compelling, smoothly flowing 4-paragraph cover letter that weaves "
                    "concrete career proof into a persuasive story tailored to the company."
                ),
                backstory=(
                    "A former editorial writer and executive career coach known for cover letters that "
                    "sound unmistakably human, grounded, and authoritative. You never write choppy, "
                    "bullet-like mini-paragraphs or repetitive 'I did X, which mirrors Y' formulas. "
                    "Instead, you connect real past roles, named companies, and measurable impact into "
                    "a natural, engaging narrative arc."
                ),
                verbose=True,
                allow_delegation=False,
                llm=get_llm_for_agent(temperature=0.7, config=candidate_config),
            )

            # ---------------------------------------------------------
            # AGENT 3: The Editor
            # Temperature: 0.3 (Low creativity, high editorial rigor)
            # Goal: Polish flow, preserve concrete names/metrics, remove AI tells.
            # ---------------------------------------------------------
            editor = Agent(
                role="Managing Editorial Director",
                goal=(
                    "Elevate prose flow, sentence rhythm, and transitions while strictly preserving "
                    "all specific employer names, metrics, and technical substance."
                ),
                backstory=(
                    "A seasoned literary and business editor with a sharp ear for rhythm and authenticity. "
                    "You eliminate robotic transitions ('Separately,', 'Furthermore,', 'In addition,'), "
                    "repetitive paragraph endings, defensive hedging ('I can adapt to...'), and AI clichés "
                    "('delve', 'testament to', 'thrilled', 'fast-paced environment'). You ensure the letter "
                    "reads like it was thoughtfully written by a top-tier professional."
                ),
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
                Analyze the candidate's CV/background and the target job posting to create an Evidence & Narrative Dossier.
                DO NOT write the cover letter yet.

                Output a structured brief containing:
                1. CORE COMPANY CHALLENGE: In 1-2 sentences, what is {company} actually building or solving with this {job_title} role?
                2. NARRATIVE THEME 1 (Primary Technical / Domain Proof): Select the 1-2 strongest achievements from the candidate's history that directly match the core role requirements. You MUST preserve exact employer/company names (e.g., "At [Company Name]..."), project contexts, technologies, and exact metrics/numbers from the candidate's background.
                3. NARRATIVE THEME 2 (Scale, Ownership & Reliability Proof): Select 1-2 complementary achievements showing system ownership, scale, collaboration, or end-to-end delivery, again preserving exact employer names and concrete outcomes.
                4. OPENING HOOK IDEA: A natural, grounded opening angle that connects the candidate's core identity and years of experience to {company}'s mission.

                STRICT RULES FOR THE ANALYST:
                - NEVER invent facts, employers, or metrics not present in the Candidate Background.
                - NEVER include a "missing skills" or "weaknesses" section. Focus 100% on what the candidate HAS achieved and how their existing mastery transfers directly to {company}'s needs.

                Job Title: {job_title}
                Company: {company}
                Job Requirements: {req_list}
                Job Description: {job_description}
                Candidate Skills: {user_skills}
                Candidate Background: {context_text or "No detailed background provided."}
                Custom Guidance: {custom_instructions if custom_instructions else "None provided."}
                """,
                expected_output=(
                    "A structured Evidence & Narrative Dossier with exact employer names, "
                    "quantified achievements grouped into 2 narrative themes, and an opening hook."
                ),
                agent=analyst,
            )

            # Task 2: Drafting (Handled by Copywriter)
            drafting_task = Task(
                description=f"""
                Using the Analyst's Evidence & Narrative Dossier and the Candidate Background below, write a standout cover letter for the {job_title} role at {company}.

                REQUIRED 4-PARAGRAPH STRUCTURE (after the salutation):
                - Salutation: Start directly with `{salutation_hint}` followed by a blank line.
                - Paragraph 1 (The Hook & Value Proposition, ~50-70 words): State the role ({job_title}) and company ({company}) naturally while leading with a strong, grounded thesis about the candidate's core expertise and why {company}'s product/engineering challenges resonate with their work.
                - Paragraph 2 (Primary Career Proof, ~85-115 words): Develop Narrative Theme 1 into a cohesive paragraph. Cite real employer names, systems built, technical stack, and measurable results from the dossier/background, weaving in naturally how this experience applies to {company}.
                - Paragraph 3 (Complementary Proof & Execution Mindset, ~75-100 words): Develop Narrative Theme 2 (e.g., large-scale pipelines, operational reliability, architecture, or cross-functional leadership) with smooth narrative flow from Paragraph 2. Show how the candidate thinks and delivers in production.
                - Paragraph 4 (Confident Call to Action, ~35-50 words): Close warmly and confidently, welcoming the opportunity to discuss how their background can support {company}'s roadmap.

                CRITICAL WRITING & FORMATTING RULES:
                1. OUTPUT BODY ONLY: Start with `{salutation_hint}` and end with Paragraph 4. Do NOT include any header, addresses, date, or closing signature ('Sincerely, [Name]')—the template system appends the signature automatically.
                2. NO CHOPPY LIST PARAGRAPHS: Write exactly 4 well-crafted body paragraphs. Never write 5-6 short, disconnected mini-paragraphs.
                3. NO REPETITIVE FORMULA: Do NOT end every paragraph with a mechanical sentence like "This mirrors {company}'s stack and shows my ability to..." or "This prepares me for {company}'s challenges." Let the achievements speak for themselves and vary how you connect them to {company}.
                4. NO DEFENSIVE / APOLOGETIC LINES: Never mention skills the candidate lacks or write defensive sentences like "My primary experience is X, though I can adapt to Y."
                5. PRESERVE REAL CONTEXT: Use the candidate's real company/employer names and concrete metrics from their background instead of vague phrases like "In a previous role" or "Separately, I built".
                6. LANGUAGE & TONE: {lang_style_guide} Total length: 240 to 340 words.
                7. CUSTOM GUIDANCE: {custom_instructions if custom_instructions else "None"}

                Candidate Background Reference:
                {context_text[:2000] if context_text else "See Analyst Dossier."}
                """,
                expected_output="A cohesive 4-paragraph cover letter body starting with the salutation and ending with a call-to-action paragraph.",
                agent=copywriter,
            )

            # Task 3: Polish (Handled by Editor)
            polish_task = Task(
                description=f"""
                Review and elevate the Copywriter's cover letter draft for {job_title} at {company}.

                EDITORIAL CHECKLIST:
                1. FLOW & COHESION: Ensure the letter consists of 3 to 4 rich, smoothly transitioning paragraphs after `{salutation_hint}`. If the draft has 5+ short or choppy paragraphs, merge related ideas into cohesive paragraphs with natural transitions.
                2. ELIMINATE ROBOTIC PATTERNS:
                   - Remove awkward transition words at the start of paragraphs ("Separately,", "Furthermore,", "Additionally,", "Moreover,").
                   - Remove repetitive tail sentences that mechanically repeat "This aligns with {company}..." or "This mirrors {company}'s stack..." at the end of multiple paragraphs.
                   - Remove any defensive or hedging statements ("I can adapt to...", "While my primary framework is...").
                   - Remove AI clichés ("delve", "testament to", "thrilled", "fast-paced environment", "hit the ground running") and replace spaced hyphens (" - ") with proper commas or periods.
                3. PRESERVE SUBSTANCE: Keep all real employer names, technologies, and concrete metrics/numbers intact. Do NOT strip out specific achievements into generic statements.
                4. STRICT BODY-ONLY FORMAT:
                   - Must begin directly with `{salutation_hint}`
                   - Must end with the final call-to-action sentence inviting a conversation/interview.
                   - Must NOT contain any header, date, address block, or sign-off ('Sincerely,', 'Best regards,', candidate name, or placeholders).
                5. LANGUAGE & WORD COUNT: Ensure fluent, idiomatic {language} ({lang_style_guide}) between 240 and 340 words.
                6. Output ONLY the final polished cover letter body text—no commentary, no markdown fences, no notes.
                """,
                expected_output="The final, publication-ready cover letter body text starting with the salutation.",
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
