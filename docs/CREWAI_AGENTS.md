# CrewAI Cover Letter Generation Workflow

Our cover letter generation is powered by a multi-agent AI system built using the **CrewAI** framework. Rather than relying on a single LLM prompt (which often leads to hallucinations or generic, bloated text), we simulate an "agency" process where specialized agents handle distinct phases of the writing pipeline.

## 👥 Agent Roster

We use three highly specialized agents, each configured with a specific "temperature" (creativity level) tailored to their role:

### 1. The Profile Analyst
- **Role:** Strategic Data Extraction
- **Temperature:** `0.1` (Very low creativity, high precision)
- **Goal:** Cross-reference the candidate's profile with the Job Description to find the 3 strongest overlaps.
- **Backstory:** A ruthless tech recruiter who only cares about cold, hard facts and perfect alignment between a candidate's history and the job's needs.

### 2. The Copywriter
- **Role:** Expert Career Coach & Storyteller
- **Temperature:** `0.7` (High creativity, persuasive)
- **Goal:** Turn the Analyst's dry brief into a cohesive, persuasive, and human-sounding cover letter narrative.
- **Backstory:** Focuses on enthusiasm and showing how the candidate's past results will solve the hiring company's future problems.

### 3. The Editor
- **Role:** Strict Copy Editor
- **Temperature:** `0.3` (Low creativity, strict formatting constraints)
- **Goal:** Final polish, cut fluff, remove AI clichés, and enforce length constraints.
- **Backstory:** Hates buzzwords and overly formal corporate speak. Aggressively removes common AI tells like "delve" or "testament to."

---

## 📋 Task Pipeline

The process runs sequentially (`Process.sequential`). The output of one task directly feeds into the context of the next.

1. **Strategy Task (Analyst)**
   - **Input:** Candidate background, skills, target company, job title, and job requirements.
   - **Action:** Does *not* write a letter. Instead, generates a structured brief identifying the 3 most relevant achievements, a suggested opening "hook," and a list of missing skills to downplay.
2. **Drafting Task (Copywriter)**
   - **Input:** The Analyst's brief.
   - **Action:** Writes the first full draft of the cover letter based *strictly* on the approved facts from the Analyst, preventing hallucinations. Applies the requested language and tone.
3. **Polish Task (Editor)**
   - **Input:** The Copywriter's draft.
   - **Action:** Strips hallucinated skills, removes sycophantic language, ensures the total length is under 300 words, and guarantees it directly addresses the hiring manager.

---

## 🔧 LLM Configuration & Resiliency

Instead of hardcoding a single provider like OpenAI, our CrewAI implementation dynamically fetches its LLM configuration from the `llm_provider_service`.

- **Dynamic Providers:** Agents can seamlessly use Groq, OpenRouter, OpenAI, or local Ollama instances depending on the active configuration.
- **Resiliency:** If a provider encounters rate limits, the system can fail over to a different model, ensuring the CrewAI pipeline remains highly reliable.
- **Hooks:** We use custom hooks to sanitize responses from OpenAI-compatible endpoints (like stripping `service_tier` from Groq) to prevent LangChain parsing errors.
