import asyncio
import os
import json
import httpx
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai import Agent

# Configuration
API_KEY = os.getenv("GROQ_API_KEY", "")
# User requested switch to Kimi
MODEL_NAME = "moonshotai/kimi-k2-instruct-0905"
BASE_URL = "https://api.groq.com/openai/v1"

# --- Baseline Prompt (Current) ---
BASELINE_SYSTEM_PROMPT = (
    "You are an expert Career Coach and Professional Writer. Your task is to write a persuasive, "
    "highly tailored cover letter based on the provided job details and candidate profile.\n\n"
    "Structure:\n"
    "1. Salutation: Professional greeting (e.g., 'Dear Hiring Manager,').\n"
    "2. Opening: State the specific role and company immediately.\n"
    "3. Body: 2-3 concise paragraphs mapping the candidate's skills and experience directly to the job requirements.\n"
    "4. Closing: Professional call to action and sign-off.\n"
    '5. Finish with "Sincerely," followed by the placeholder "[Your Name]" exactly. Do NOT use the candidate\'s real name.\n\n'
    "Constraints:\n"
    "- Tone: Professional, confident, and business-appropriate.\n"
    "- Format: PLAIN TEXT ONLY. No Markdown, no bolding, no headers, and no placeholders (e.g., [Company]).\n"
    "- Length: 200-400 words.\n"
    "- Quality: Focus on impact and specific achievements. Avoid generic fluff.\n"
    "- Output: Return ONLY the cover letter text. No introductory remarks or meta-commentary."
)

# --- Improved Prompt (Few-Shot) ---
EXAMPLE_LETTER = """Dear Hiring Manager,

I am writing to express my strong interest in the Senior Software Engineer position at TechFlow, as advertised. With over six years of experience building scalable distributed systems and a deep expertise in Python and cloud architecture, I am confident in my ability to hit the ground running and contribute immediately to your engineering team.

In my current role at DataSystems, I led the migration of a monolithic legacy application to a microservices architecture using Python and AWS, which helped reduce deployment time by 40% and improved system reliability. I also spearheaded the adoption of Docker for our development environments, ensuring consistent testing and production deployments. My technical background in high-performance computing directly aligns with TechFlow's mission to process real-time data at scale.

Beyond my technical skills, I pride myself on being a proactive collaborator. I have successfully mentored three junior developers, guiding them through complex architectural decisions and code reviews. I am eager to bring this same dedication to technical excellence and team growth to TechFlow.

Thank you for considering my application. I welcome the opportunity to discuss how my background in backend engineering and cloud infrastructure can support TechFlow’s upcoming product roadmap.

Sincerely,
[Your Name]"""

IMPROVED_SYSTEM_PROMPT = f"""You are an elite Career Coach known for writing compelling, high-impact cover letters that get candidates hired.

Your Goal: Write a cover letter that proves the candidate is the *perfect match* for the role.

INSTRUCTIONS:
1. **Analyze** the Job Requirements and Candidate Skills. Find the strongest matches.
2. **Write** a letter that sounds human, professional, and confident. Avoid robotic phrases like "I am a perfect fit" or "I am excited to apply". Instead, *show* the fit.
3. **Structure**:
   - Salutation
   - Hook (Opening): Mention the role/company and a key value proposition immediately.
   - Evidence (Body): Use specific skills/experiences to prove the candidate can solve the company's problems.
   - Call to Action (Closing): confident sign-off.
   - Signature: 'Sincerely,' followed by the placeholder '[Your Name]'.

EXAMPLE OF QUALITY (Do not copy, but mimic the tone and structure):
---
{EXAMPLE_LETTER}
---

CONSTRAINTS:
- No placeholders.
- No markdown.
- 200-350 words.
- Tone: Professional, direct, results-oriented.
"""

# Test Data
USER_INPUT = """Write a professional cover letter for Sarah Jenkins applying to CloudNine as a DevOps Engineer.

7. Finish with "Sincerely," followed by the placeholder "[Your Name]" exactly. Do NOT use the candidate's real name.

Job Requirements: AWS, Kubernetes, CI/CD pipelines, Terraform.
Candidate Skills: 5 years DevOps experience, AWS Certified Pro, extensive Kubernetes management, Terraform expert, built CI/CD for fintech startup.
"""


# Hook to fix Groq compatibility issue
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


async def run_test(name, prompt):
    print(f"\n🏃 Running {name}...")

    http_client = httpx.AsyncClient(event_hooks={"response": [strip_service_tier_hook]})
    provider = OpenAIProvider(
        base_url=BASE_URL, api_key=API_KEY, http_client=http_client
    )
    model = OpenAIChatModel(model_name=MODEL_NAME, provider=provider)
    agent = Agent(model, system_prompt=prompt)

    try:
        result = await agent.run(USER_INPUT)
        output = (
            result.data
            if hasattr(result, "data")
            else str(result.data)
            if hasattr(result, "data")
            else str(result.output)
            if hasattr(result, "output")
            else str(result)
        )

        print(f"\n--- {name} RESULT ---")
        print(output)
        print("-" * 30)
        return output
    except Exception as e:
        print(f"❌ {name} Failed: {e}")
        return None


async def main():
    print(f"🧪 Benchmarking Quality for {MODEL_NAME}")

    await run_test("BASELINE", BASELINE_SYSTEM_PROMPT)
    await run_test("IMPROVED (FEW-SHOT)", IMPROVED_SYSTEM_PROMPT)


if __name__ == "__main__":
    asyncio.run(main())
