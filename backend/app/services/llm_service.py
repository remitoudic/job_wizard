import os
import asyncio
import uuid
from typing import Optional, Dict, Any

from app.services.agents import create_writing_agent, create_extraction_agent, ContactInfo

class LLMService:
    """Service for generating cover letters using Pydantic AI Agents"""
    
    def __init__(self):
        # Configuration
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        self.ollama_model_name = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
        
        # Initialize Agents
        self.local_writer = create_writing_agent(self.ollama_model_name, is_remote=False)
        self.remote_writer = None
        if self.openrouter_api_key:
            self.remote_writer = create_writing_agent(self.openrouter_model_name, is_remote=True)
            
        # Extraction Agent (Use local for privacy/speed usually, or remote if configured)
        # Using local for parsing to save free tier limits
        self.extractor = create_extraction_agent(self.ollama_model_name, base_url=self.ollama_host)

        self.alternatives_store = {} # Simple in-memory store
    
    async def extract_contact_info(self, text: str) -> Dict[str, Any]:
        """
        Extract contact info using Pydantic AI Agent
        """
        try:
            # Agent.run is async
            result = await self.extractor.run(text)
            return result.data.model_dump()
        except Exception as e:
            print(f"Extraction failed: {e}")
            return {}

    async def generate_cover_letter(
        self,
        job_description: str,
        job_title: str,
        company: str,
        requirements: list[str],
        user_name: str = "Applicant",
        user_skills: str = "",
        context_text: Optional[str] = None,
    ) -> tuple[str, str, str]:
        """
        Generate cover letter with race mode (Local vs Remote)
        """
        # Build prompt
        prompt = f"""
        JOB TITLE: {job_title}
        COMPANY: {company}
        DESCRIPTION: {job_description}
        REQUIREMENTS: {', '.join(requirements)}
        
        CANDIDATE NAME: {user_name}
        CANDIDATE SKILLS: {user_skills}
        """
        if context_text:
            prompt += f"\nRESUME/CONTEXT: {context_text[:3000]}"

        tasks = []
        
        # Task 1: Local
        local_task = asyncio.create_task(
            self.local_writer.run(prompt), 
            name=f"Ollama ({self.ollama_model_name})"
        )
        tasks.append(local_task)
        
        # Task 2: Remote
        if self.remote_writer:
            remote_task = asyncio.create_task(
                self.remote_writer.run(prompt),
                name=f"OpenRouter ({self.openrouter_model_name})"
            )
            tasks.append(remote_task)
            
        if not tasks:
            raise Exception("No generation agents available")

        # Race
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        winner_task = done.pop()
        try:
            winner_result = await winner_task
            winner_text = winner_result.data # .data holds the str result
            winner_source = winner_task.get_name()
        except Exception as e:
            # If winner failed, try waiting for others or raise
            raise Exception(f"Winner task failed: {e}")
            
        # Process alternatives
        alt_id = str(uuid.uuid4())
        if pending:
            asyncio.create_task(self._process_alternatives(pending, alt_id))
            return winner_text, winner_source, alt_id
            
        return winner_text, winner_source, ""

    async def _process_alternatives(self, pending_tasks, alt_id: str):
        """Handle the slower tasks"""
        try:
            done, _ = await asyncio.wait(pending_tasks, return_when=asyncio.ALL_COMPLETED)
            for task in done:
                try:
                    res = await task
                    self.alternatives_store[alt_id] = {
                        "text": res.data,
                        "source": task.get_name()
                    }
                    break # Just store one alternative for now
                except Exception as e:
                    print(f"Alternative task failed: {e}")
        except Exception as e:
            print(f"Error processing alternatives: {e}")

    def get_alternative(self, alt_id: str) -> Optional[Dict[str, str]]:
        return self.alternatives_store.get(alt_id)
