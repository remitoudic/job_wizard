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
        event_hooks={"response": [strip_service_tier_hook]}
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
        # Dynamic Remote Provider (OpenRouter or Cerebras)
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
    
    agent = Agent(
        model,
        output_type=str,
        # Optimized system prompt - more concise and direct
        system_prompt=(
            "You are a professional career coach. Generate a cover letter body following this EXACT structure:\n"
            "1. Salutation (e.g. 'Dear Hiring Manager,')\n"
            "2. Opening: State role and company.\n"
            "3. Body Paragraphs: 2-3 paragraphs highlighting relevance of candidate skills to requirements.\n"
            "4. Closing: Professional sign-off.\n"
            "5. Signature: 'Sincerely,' followed by the candidate's name on a new line.\n\n"
            "Constraints:\n"
            "- Tone: Formal and business-appropriate.\n"
            "- Length: 200–400 words.\n"
            "- Content: Clarity and impact. No verbosity.\n"
            "- Formatting: Plain text only. NO markdown. NO headings. NO meta commentary."
        ),
        # Speed optimization parameters
        model_settings={
            "temperature": 0.2,      # Lower temperature for better instruction following
            "max_tokens": 500,       # Limit output length
            "top_p": 0.9,           # Nucleus sampling for speed
        }
    )
    return agent
