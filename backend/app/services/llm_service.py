import os
import asyncio
import uuid
from typing import Optional, Dict, Any

from app.services.agents import create_writing_agent, create_extraction_agent, ContactInfo
import logfire

class LLMService:
    """Service for generating cover letters using Pydantic AI Agents"""
    
    def __init__(self):
        # Configuration
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        self.ollama_model_name = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model_name = os.getenv("OPENROUTER_MODEL", "xiaomi/mimo-v2-flash:free")
        self.openrouter_model_name_2 = os.getenv("OPENROUTER_MODEL_2", "meta-llama/llama-3.3-70b-instruct:free")
        
        # Initialize Agents
        self.local_writer = create_writing_agent(self.ollama_model_name, is_remote=False)
        self.remote_writer = None
        self.remote_writer_2 = None
        if self.openrouter_api_key:
            self.remote_writer = create_writing_agent(self.openrouter_model_name, is_remote=True)
            self.remote_writer_2 = create_writing_agent(self.openrouter_model_name_2, is_remote=True)
            
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
            logfire.info("Starting contact extraction")
            result = await self.extractor.run(text)
            return result.output.model_dump()
        except Exception as e:
            print(f"Extraction failed: {e}")
            return {}

    async def generate_cover_letter(
        self,
        job_description: str,
        job_title: str,
        company: str,
        requirements: list[str],
        user_name: str = "",
        user_skills: str = "",
        context_text: Optional[str] = None,
    ) -> tuple[str, str, str]:
        """
        Generate cover letter with race mode (Local vs Remote)
        """
        import time
        
        # Build optimized prompt (concise for speed)
        req_list = ', '.join(requirements[:5]) if requirements else 'See description'
        
        name_placeholder = f"for {user_name}" if user_name else ""
        prompt = f"""Write a professional cover letter {name_placeholder} applying to {company} as {job_title}.

IMPORTANT: 
1. If you don't know the candidate's name, DO NOT use a placeholder like "[Your Name]". Start directly with the address/salutation.
2. DO NOT use placeholders for date like "[Date]".
3. Return ONLY the letter body.

Key requirements: {req_list}
Candidate skills: {user_skills}
"""
        if context_text:
            # Reduced from 3000 to 1500 chars for faster processing
            prompt += f"\nCandidate background:\n{context_text[:1500]}"

        tasks = []
        task_start_times = {}
        
        logfire.info(
            "Starting generation race", 
            model_local=self.ollama_model_name, 
            model_remote_1=self.openrouter_model_name if self.remote_writer else "none",
            model_remote_2=self.openrouter_model_name_2 if self.remote_writer_2 else "none"
        )
        
        race_start = time.perf_counter()
        
        # Task 1: Local
        local_task = asyncio.create_task(
            self.local_writer.run(prompt), 
            name=f"Ollama ({self.ollama_model_name})"
        )
        task_start_times[id(local_task)] = time.perf_counter()
        tasks.append(local_task)
        
        # Task 2: Remote (OpenRouter Model 1)
        if self.remote_writer:
            remote_task = asyncio.create_task(
                self.remote_writer.run(prompt),
                name=f"OpenRouter ({self.openrouter_model_name})"
            )
            task_start_times[id(remote_task)] = time.perf_counter()
            tasks.append(remote_task)
        
        # Task 3: Remote (OpenRouter Model 2)
        if self.remote_writer_2:
            remote_task_2 = asyncio.create_task(
                self.remote_writer_2.run(prompt),
                name=f"OpenRouter ({self.openrouter_model_name_2})"
            )
            task_start_times[id(remote_task_2)] = time.perf_counter()
            tasks.append(remote_task_2)
            
        if not tasks:
            raise Exception("No generation agents available")

        # Race
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        race_duration = time.perf_counter() - race_start
        
        winner_task = done.pop()
        try:
            winner_result = await winner_task
            winner_text = winner_result.output # .output holds the result
            winner_source = winner_task.get_name()
            winner_duration = time.perf_counter() - task_start_times[id(winner_task)]
            
            logfire.info(
                "Race won", 
                winner=winner_source,
                winner_duration_seconds=round(winner_duration, 2),
                race_duration_seconds=round(race_duration, 2)
            )
            print(f"🏁 RACE WINNER: {winner_source} in {winner_duration:.2f}s")
        except Exception as e:
            logfire.error("Race winner failed", error=str(e))
            # If winner failed, try waiting for others or raise
            raise Exception(f"Winner task failed: {e}")
            
        # Process alternatives
        alt_id = str(uuid.uuid4())
        if pending:
            asyncio.create_task(self._process_alternatives(pending, alt_id, task_start_times))
            return winner_text, winner_source, alt_id
            
        return winner_text, winner_source, ""

    async def _process_alternatives(self, pending_tasks, alt_id: str, task_start_times: dict):
        """Handle the slower tasks"""
        import time
        try:
            done, _ = await asyncio.wait(pending_tasks, return_when=asyncio.ALL_COMPLETED)
            alternatives = []
            for task in done:
                try:
                    res = await task
                    task_duration = time.perf_counter() - task_start_times.get(id(task), 0)
                    alternative = {
                        "text": res.output,
                        "source": task.get_name(),
                        "status": "completed"
                    }
                    alternatives.append(alternative)
                    logfire.info(
                        "Alternative completed", 
                        id=alt_id, 
                        source=task.get_name(),
                        duration_seconds=round(task_duration, 2)
                    )
                    print(f"⏱️  Alternative completed: {task.get_name()} in {task_duration:.2f}s")
                except Exception as e:
                    # Include failed tasks so user sees all participants
                    task_duration = time.perf_counter() - task_start_times.get(id(task), 0)
                    alternative = {
                        "text": f"Generation failed: {str(e)}",
                        "source": task.get_name(),
                        "status": "failed"
                    }
                    alternatives.append(alternative)
                    logfire.error("Alternative task failed", source=task.get_name(), error=str(e))
                    print(f"❌ Alternative task failed [{task.get_name()}]: {e}")
            
            # Store all alternatives
            if alternatives:
                self.alternatives_store[alt_id] = alternatives
        except Exception as e:
            logfire.error("Error processing alternatives", error=str(e))
            print(f"Error processing alternatives: {e}")

    def get_alternative(self, alt_id: str) -> Optional[Dict[str, str]]:
        return self.alternatives_store.get(alt_id)
