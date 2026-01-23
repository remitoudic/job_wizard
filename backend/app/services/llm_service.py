import os
import asyncio
import uuid
from typing import Optional, Dict, Any

from app.services.agents import create_writing_agent, create_extraction_agent, ContactInfo
from app.core.config import settings
import logfire

class LLMService:
    """Service for generating cover letters using Pydantic AI Agents"""
    
    def __init__(self):
        # Configuration
        self.ollama_host = settings.OLLAMA_HOST
        self.ollama_model_name = settings.OLLAMA_MODEL
        
        self.openrouter_api_key = settings.OPENROUTER_API_KEY
        self.openrouter_model_name = settings.OPENROUTER_MODEL
        self.openrouter_model_name_2 = settings.OPENROUTER_MODEL_2
        
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
        import logging
        
        # Configure logger
        logger = logging.getLogger("app.services.llm_service")
        
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
        logger.info(f"Starting generic race with local={self.ollama_model_name}")
        
        race_start = time.perf_counter()
        
        # Helper to wrap agent run with source info
        async def run_agent(agent, p, name):
            res = await agent.run(p)
            return {"output": res.output, "source": name}

        # Task 1: Local
        local_task = asyncio.create_task(
            run_agent(self.local_writer, prompt, f"Ollama ({self.ollama_model_name})"), 
            name=f"Ollama ({self.ollama_model_name})"
        )
        task_start_times[id(local_task)] = time.perf_counter()
        tasks.append(local_task)
        
        # Task 2: Remote (OpenRouter Model 1)
        if self.remote_writer:
            remote_task = asyncio.create_task(
                 run_agent(self.remote_writer, prompt, f"OpenRouter ({self.openrouter_model_name})"),
                name=f"OpenRouter ({self.openrouter_model_name})"
            )
            task_start_times[id(remote_task)] = time.perf_counter()
            tasks.append(remote_task)
        
        # Task 3: Remote (OpenRouter Model 2)
        if self.remote_writer_2:
            remote_task_2 = asyncio.create_task(
                run_agent(self.remote_writer_2, prompt, f"OpenRouter ({self.openrouter_model_name_2})"),
                name=f"OpenRouter ({self.openrouter_model_name_2})"
            )
            task_start_times[id(remote_task_2)] = time.perf_counter()
            tasks.append(remote_task_2)
            
        if not tasks:
            raise Exception("No generation agents available")

        race_duration = time.perf_counter() - race_start
        
        winner_text = None
        winner_source = None
        failed_attempts = []
        finished_alternatives = [] # To store successes that weren't the winner (if any)
        
        # Race loop
        while tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            for task in done:
                try:
                    result = await task
                    if not winner_text:
                        # We have our first winner!
                        winner_text = result["output"]
                        winner_source = result["source"]
                        winner_duration = time.perf_counter() - task_start_times[id(task)]
                        logfire.info(
                            "Race won", 
                            winner=winner_source,
                            winner_duration_seconds=round(winner_duration, 2),
                            race_duration_seconds=round(race_duration, 2),
                            failed_attempts=len(failed_attempts)
                        )
                        logger.info(f"Race won by {winner_source} in {winner_duration:.2f}s")
                    else:
                        # Already have a winner, this is an alternative
                        finished_alternatives.append({
                            "text": result["output"],
                            "source": result["source"],
                            "status": "completed"
                        })
                        
                except Exception as e:
                    failed_source = task.get_name()
                    failed_attempts.append({"source": failed_source, "error": str(e)})
                    logger.warning(f"Model failed: {failed_source} - {e}")
                    logfire.warning("Model failed", source=failed_source, error=str(e))
            
            if winner_text:
                # We have a winner, remainder are pending alternatives
                # Exit the main race loop
                break
            else:
                # No winner yet (all in 'done' failed), continue with pending
                tasks = list(pending)
        
        # Logic to handle race end (either winner found or all failed)

        if winner_text is None:
            error_summary = "; ".join([f"{f['source']}: {f['error']}" for f in failed_attempts])
            logfire.error("All models failed", failures=failed_attempts)
            raise Exception(f"All models failed. Errors: {error_summary}")
            
        # Success!
        logfire.info(
            "Race won", 
            winner=winner_source,
            winner_duration_seconds=round(winner_duration, 2),
            race_duration_seconds=round(race_duration, 2)
        )
        logger.info(f"Race won by {winner_source} in {winner_duration:.2f}s")
        
        # Handle Alternatives
        # 1. pending tasks (still running)
        # 2. finished_alternatives (finished successfully but not winner, or failed during fallback)
        # 3. failed_attempts (failed during initial race) - we can choose to show these or not.
        
        alt_id = str(uuid.uuid4())
        
        # Populate store initially with what we have
        current_alts = []
        for alt in finished_alternatives:
             current_alts.append(alt)
             
        # Add initial failures to alternatives too, for completeness?
        # The user might want to know if a model failed.
        for fail in failed_attempts:
            # Check if not already added (fallback logic adds failures to finished_alternatives)
            if not any(a["source"] == fail["source"] for a in current_alts):
                current_alts.append({
                    "text": f"Generation failed: {fail['error']}",
                    "source": fail["source"],
                    "status": "failed"
                })
                
        # Store initial state
        self.alternatives_store[alt_id] = {
            "status": "pending" if pending else "completed",
            "alternatives": current_alts
        }
        
        # If there are still running tasks (pending), wait for them in background
        if pending:
            asyncio.create_task(self._process_alternatives(pending, alt_id, task_start_times))
            
        return winner_text, winner_source, alt_id

    async def _process_alternatives(self, pending_tasks, alt_id: str, task_start_times: dict):
        """Handle the slower tasks incrementally"""
        import time
        import logging
        logger = logging.getLogger("app.services.llm_service")
        
        # Initialize tasks set
        tasks = list(pending_tasks)
        
        try:
            while tasks:
                # Wait for the next one to complete
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                
                # Get current state
                state = self.alternatives_store.get(alt_id, {"status": "pending", "alternatives": []})
                current_alternatives = state.get("alternatives", [])
                
                for task in done:
                    try:
                        result = await task
                        # result is dict because of run_agent wrapper
                        task_duration = time.perf_counter() - task_start_times.get(id(task), 0)
                        
                        alt = {
                            "text": result["output"],
                            "source": result["source"],
                            "status": "completed"
                        }
                        current_alternatives.append(alt)
                        logfire.info(
                            "Alternative completed", 
                            id=alt_id, 
                            source=result["source"],
                            duration_seconds=round(task_duration, 2)
                        )
                        logger.info(f"Alternative completed: {result['source']} in {task_duration:.2f}s")
                    except Exception as e:
                        task_duration = time.perf_counter() - task_start_times.get(id(task), 0)
                        alt = {
                            "text": f"Generation failed: {str(e)}",
                            "source": task.get_name(),
                            "status": "failed"
                        }
                        current_alternatives.append(alt)
                        logger.error(f"Alternative failed: {task.get_name()} - {e}")
                
                # Update store incrementally
                self.alternatives_store[alt_id] = {
                    "status": "pending" if pending else "completed",
                    "alternatives": current_alternatives
                }
                
                # Continue with remaining
                tasks = list(pending)
            
        except Exception as e:
            logfire.error("Error processing alternatives", error=str(e))
            logger.error(f"Error processing alternatives: {e}")
            # Ensure we mark as completed even on error, or failed?
            state = self.alternatives_store.get(alt_id)
            if state:
                state["status"] = "completed"
                self.alternatives_store[alt_id] = state

    def get_alternative(self, alt_id: str) -> Optional[Dict]:
        return self.alternatives_store.get(alt_id)
