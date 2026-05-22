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

def get_llm_for_agent(temperature: float) -> ChatOpenAI:
    """
    Constructs the LangChain LLM instance dynamically.
    
    Why dynamic?
    Instead of hardcoding OpenAI, we fetch the active provider config (Groq, OpenRouter, etc.)
    from our `llm_provider_service`. This allows the CrewAI agents to smoothly failover
    if a provider hits rate limits, ensuring maximum reliability.

    Args:
        temperature (float): The creativity setting. 0.1 for analytical, 0.7 for creative.
    """
    config = llm_provider_service.get_provider_config()
    
    # Grab the primary model defined in the active provider's config
    model_name = config.get("model_1", "llama3-8b-8192")
    
    # Initialize the HTTP clients with our Groq-compatibility hooks
    client = httpx.Client(event_hooks={"response": [strip_service_tier_hook_sync]}, timeout=120.0)
    async_client = httpx.AsyncClient(event_hooks={"response": [strip_service_tier_hook_async]}, timeout=120.0)
    
    # We omit `max_tokens` here because some LLM providers (like NVIDIA NIM) throw errors 
    # if `max_completion_tokens` is provided in an incompatible format.
    return ChatOpenAI(
        model=model_name,
        api_key=config["api_key"],
        base_url=config["base_url"],
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
    language: str = "english"
) -> str:
    """
    Kicks off the Sequential CrewAI process to generate a cover letter.
    
    This function initializes three distinct agents with varying "temperatures" 
    (creativity levels) to simulate a real-world writing pipeline.
    """
    logger.info(f"Starting CrewAI generation for {company} - {job_title}")
    
    req_list = ", ".join(requirements) if requirements else "See description"
    
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
        llm=get_llm_for_agent(temperature=0.1)
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
        llm=get_llm_for_agent(temperature=0.7)
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
        llm=get_llm_for_agent(temperature=0.3)
    )
    
    # ---------------------------------------------------------
    # TASK DEFINITIONS
    # The output of one task becomes the context for the next in a sequential process.
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
        Candidate Background: {context_text or 'No detailed background provided.'}
        """,
        expected_output="A structured brief detailing the 3 strongest overlaps, a hook, and skills to downplay.",
        agent=analyst
    )
    
    # Task 2: Drafting (Handled by Copywriter)
    drafting_task = Task(
        description=f"""
        Write the first draft of the cover letter based ONLY on the points provided in the Analyst's brief.
        Use a confident, professional, yet approachable tone. 
        Show how the candidate's past results will solve the company's problems.
        The letter should be written in {language}.
        Target Company: {company}
        Target Role: {job_title}
        Candidate Name: {user_name if user_name else '[Your Name]'}
        """,
        expected_output="A full draft of a cover letter.",
        agent=copywriter
    )
    
    # Task 3: Polish (Handled by Editor)
    polish_task = Task(
        description=f"""
        Review the draft cover letter from the copywriter.
        1. Strip out any hallucinated skills not in the original brief.
        2. Remove sycophantic language or obvious AI tells (e.g., 'delve', 'testament to', 'thrilled to apply').
        3. Ensure the letter is under 300 words.
        4. Ensure it directly addresses the hiring manager.
        5. Ensure the final language is {language}.
        6. Do NOT output anything other than the final cover letter text.
        """,
        expected_output="The final, polished cover letter ready to be sent.",
        agent=editor
    )
    
    # ---------------------------------------------------------
    # CREW ASSEMBLY & EXECUTION
    # ---------------------------------------------------------
    
    cover_letter_crew = Crew(
        agents=[analyst, copywriter, editor],
        tasks=[strategy_task, drafting_task, polish_task],
        process=Process.sequential,  # Tasks execute in exact order
        verbose=True
    )
    
    # Kickoff is synchronous. In our llm_service.py, we wrap this in `asyncio.to_thread` 
    # to ensure it doesn't block the main Temporal.io event loop.
    result = cover_letter_crew.kickoff()
    
    logger.info("CrewAI generation completed.")
    return str(result)

