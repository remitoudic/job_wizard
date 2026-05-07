import os
import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import httpx
import json
from typing import Optional

# Hook to fix Groq compatibility issue (unexpected service_tier field)
async def strip_service_tier_hook(response: httpx.Response):
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

def create_custom_openai_provider(base_url: str, api_key: str) -> OpenAIProvider:
    client = httpx.AsyncClient(
        event_hooks={"response": [strip_service_tier_hook]},
        timeout=120.0
    )
    return OpenAIProvider(base_url=base_url, api_key=api_key, http_client=client)


# Configure Logfire
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"), send_to_logfire='if-token-present')

# --- Models ---

class ContactInfo(BaseModel):
    name: Optional[str] = Field("", description="Full name of the candidate")
    first_name: Optional[str] = Field("", description="First name of the candidate")
    surname: Optional[str] = Field("", description="Surname/last name of the candidate")
    email: Optional[str] = Field("", description="Email address")
    phone: Optional[str] = Field("", description="Phone number")
    linkedin: Optional[str] = Field("", description="LinkedIn profile URL")
    website: Optional[str] = Field("", description="Personal website or portfolio URL")
    address: Optional[str] = Field("", description="Physical address or location (City, State)")
    address_street: Optional[str] = Field("", description="Street address")
    address_postcode: Optional[str] = Field("", description="Postcode/Zip code")
    address_city: Optional[str] = Field("", description="City")
    address_country: Optional[str] = Field("", description="Country")

class JobDetails(BaseModel):
    job_description: str
    job_title: str
    company: str
    requirements: list[str]
    user_name: str
    user_skills: str
    context_text: Optional[str] = None

class CoverLetterResult(BaseModel):
    content: str = Field(..., description="The generated cover letter text")
    model_name: str = Field("unknown", description="Name of the model that generated this")

# --- Prompts ---

SIMPLE_SYSTEM_PROMPT = (
    "You are a professional Career Coach. Write a concise, professional cover letter based on the job details.\n"
    "Structure:\n"
    "1. Salutation (e.g. 'Dear Hiring Manager,')\n"
    "2. Hook: State role and company.\n"
    "3. Body: 2 paragraphs matching skills to requirements.\n"
    "4. Closing: Professional sign-off.\n"
    "5. Signature: 'Sincerely,' followed by '[Your Name]'.\n\n"
    "Constraints:\n"
    "- Tone: Professional and direct.\n"
    "- Format: PLAIN TEXT ONLY. No placeholders.\n"
    "- Length: 150-250 words.\n"
    "- Output: The cover letter ONLY. No intro/outro.\n"
    "- Finish with: 'Sincerely,\n[Your Name]'"
)

FEW_SHOT_EXAMPLE = """
Dear Hiring Manager,

I am writing to express my strong interest in the Senior Software Engineer position at TechFlow, as advertised. With over six years of experience building scalable distributed systems and a deep expertise in Python and cloud architecture, I am confident in my ability to hit the ground running and contribute immediately to your engineering team.

In my current role at DataSystems, I led the migration of a monolithic legacy application to a microservices architecture using Python and AWS, which helped reduce deployment time by 40% and improved system reliability. I also spearheaded the adoption of Docker for our development environments, ensuring consistent testing and production deployments. My technical background in high-performance computing directly aligns with TechFlow's mission to process real-time data at scale.

Beyond my technical skills, I pride myself on being a proactive collaborator. I have successfully mentored three junior developers, guiding them through complex architectural decisions and code reviews. I am eager to bring this same dedication to technical excellence and team growth to TechFlow.

Thank you for considering my application. I welcome the opportunity to discuss how my background in backend engineering and cloud infrastructure can support TechFlow’s upcoming product roadmap.

Sincerely,
[Your Name]
"""

# --- Agents ---

def create_extraction_agent(model_name: str = "llama3.2:1b", base_url: str = "http://ollama:11434/v1") -> Agent:
    """
    Creates an agent for extracting contact info.
    Uses OpenAIModel for both Local (Ollama) and Remote (OpenRouter) as Ollama supports OpenAI API.
    """
    
    if "ollama" in base_url or "localhost" in base_url:
        # Local Ollama via OpenAI API
        # Ensure base_url ends with /v1
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
            
        # provider = OpenAIProvider(base_url=base_url, api_key="ollama") # Dummy key required
        provider = create_custom_openai_provider(base_url=base_url, api_key="ollama")
        model = OpenAIChatModel(model_name=model_name, provider=provider)
    else:
        # Remote OpenRouter
        # provider = OpenAIProvider(
        #     base_url="https://openrouter.ai/api/v1",
        #     api_key=os.getenv("OPENROUTER_API_KEY")
        # )
        provider = create_custom_openai_provider(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        model = OpenAIChatModel(model_name=model_name, provider=provider)

    agent = Agent(
        model,
        output_type=ContactInfo,
        system_prompt=(
            "You are an expert HR data parser. Extract contact information from the provided resume text. "
            "Return JSON matching the schema. If a field is missing, return an empty string."
        )
    )
    # logfire.instrument_pydantic(ContactInfo)
    return agent

def create_writing_agent(model_name: str, is_remote: bool = False, provider_config: Optional[dict] = None) -> Agent:
    """
    Creates an agent for writing cover letters with optimized parameters for speed.
    Allows dynamic provider configuration for failover.
    """
    if not is_remote:
        # Local Ollama
        host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        if not host.endswith("/v1"):
            host = f"{host}/v1"
            
        # provider = OpenAIProvider(base_url=host, api_key="ollama")
        provider = create_custom_openai_provider(base_url=host, api_key="ollama")
        model = OpenAIChatModel(model_name=model_name, provider=provider)
    elif provider_config:
        # Dynamic Remote Provider (Groq or OpenRouter)
        # provider = OpenAIProvider(
        #     base_url=provider_config["base_url"],
        #     api_key=provider_config["api_key"]
        # )
        provider = create_custom_openai_provider(
            base_url=provider_config["base_url"],
            api_key=provider_config["api_key"]
        )
        model = OpenAIChatModel(model_name=model_name, provider=provider)
    else:
        # Fallback to default OpenRouter (legacy behavior)
        # provider = OpenAIProvider(
        #     base_url="https://openrouter.ai/api/v1",
        #     api_key=os.getenv("OPENROUTER_API_KEY")
        # )
        provider = create_custom_openai_provider(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        model = OpenAIChatModel(model_name=model_name, provider=provider)
    
    # Define default system prompt (Complex/Few-Shot)
    system_prompt = (
        "You are an expert Career Coach and Professional Writer. Your task is to write a persuasive, "
        "highly tailored cover letter based on the provided job details and candidate profile.\n\n"
        "Structure:\n"
        "1. Salutation: Professional greeting (e.g., 'Dear Hiring Manager,').\n"
        "2. Opening: Hook the reader by stating the role/company and a key value proposition immediately.\n"
        "3. Body: 2-3 concise paragraphs mapping the candidate's skills and experience directly to the job requirements. Use specific accomplishments.\n"
        "4. Closing: Professional call to action and sign-off.\n"
        "5. Signature: 'Sincerely,' followed by the placeholder '[Your Name]'.\n\n"
        "EXAMPLE OF HIGH QUALITY (Mimic the tone and structure, do NOT copy content):\n"
        "--------------------------------------------------\n"
        f"{FEW_SHOT_EXAMPLE}\n"
        "--------------------------------------------------\n\n"
        "Constraints:\n"
        "- Tone: Professional, confident, and business-appropriate. Avoid robotic phrases.\n"
        "- Format: PLAIN TEXT ONLY. No Markdown, no bolding, no headers, and no placeholders.\n"
        "- Length: 200-400 words.\n"
        "- Quality: Focus on impact and specific achievements. Avoid generic fluff.\n"
        "- Output: Return ONLY the cover letter text. No introductory remarks or meta-commentary. Use '[Your Name]' as the signature."
    )

    # Optimized system prompt - more concise and direct
    model_settings = {
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 0.9,
    }

    if not is_remote:
        system_prompt = SIMPLE_SYSTEM_PROMPT
        # Reduce max tokens for local model to speed up generation (shorter letter)
        model_settings["max_tokens"] = 300
        
    # NVIDIA NIM models (like qwen) may reject max_completion_tokens
    if is_remote and provider_config and provider_config.get("name") == "nvidia":
        model_settings.pop("max_tokens", None)

    agent = Agent(
        model,
        output_type=str,
        system_prompt=system_prompt,
        model_settings=model_settings
    )
    return agent
