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
        
        # Import here to avoid circular dependencies if any
        from app.services.llm_provider_service import llm_provider_service
        self.provider_service = llm_provider_service
        
        # Initialize Agents
        self.local_writer = create_writing_agent(self.ollama_model_name, is_remote=False)
        self.remote_writer = None
        self.remote_writer_2 = None
        
        # Remote agents are now created dynamically per request based on active provider
        # to support failover.
            
        # Extraction Agent (Use local for privacy/speed usually, or remote if configured)
        # Using local for parsing to save free tier limits
        self.extractor = create_extraction_agent(self.ollama_model_name, base_url=self.ollama_host)

        self.alternatives_store = {} # Simple in-memory store
        self.background_tasks = set()

    def cleanup(self):
        """Cancel all running background tasks"""
        for task in self.background_tasks:
            task.cancel()
        self.background_tasks.clear()
    
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
3. Return ONLY the letter body. Do not use markdown code blocks or introductory text.
4. Use a very  formal tone.
5. Keep the letter between 200 and 400 words.
6. Maintain a formal, business-appropriate tone. 
7. finish with "Sincerely," or "Best regards," and the candidate's name.

Key requirements: {req_list}
Candidate skills: {user_skills}
"""
        if context_text:
            # Reduced from 3000 to 1500 chars for faster processing
            prompt += f"\nCandidate background:\n{context_text[:1500]}"

        # Retry loop for failover
        max_retries = 1
        attempt = 0
        
        while attempt <= max_retries:
            attempt += 1
            
            # Get active provider configuration
            remote_config = self.provider_service.get_provider_config()
            self.current_provider_name = remote_config["name"]
            
            logfire.info(
                "Starting generation race", 
                model_local=self.ollama_model_name, 
                active_provider=self.current_provider_name,
                model_remote_1=remote_config["model_1"],
                model_remote_2=remote_config["model_2"],
                attempt=attempt
            )
            
            # Only log attempt if it's a retry
            retry_msg = f" (Attempt {attempt})" if attempt > 1 else ""
            logger.info(f"Starting generic race with local={self.ollama_model_name} and remote_provider={self.current_provider_name}{retry_msg}")
            
            race_start = time.perf_counter()
            tasks = []
            task_start_times = {}
            
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
            
            # Create Remote Agents dynamically
            try:
                # Remote Agent 1
                remote_writer = create_writing_agent(
                    model_name=remote_config["model_1"], 
                    is_remote=True,
                    provider_config=remote_config
                )
                remote_task = asyncio.create_task(
                     run_agent(remote_writer, prompt, f"{self.current_provider_name.title()} ({remote_config['model_1']})"),
                    name=f"{self.current_provider_name.title()} ({remote_config['model_1']})"
                )
                task_start_times[id(remote_task)] = time.perf_counter()
                tasks.append(remote_task)
                
                # Remote Agent 2
                remote_writer_2 = create_writing_agent(
                    model_name=remote_config["model_2"], 
                    is_remote=True,
                    provider_config=remote_config
                )
                remote_task_2 = asyncio.create_task(
                    run_agent(remote_writer_2, prompt, f"{self.current_provider_name.title()} ({remote_config['model_2']})"),
                    name=f"{self.current_provider_name.title()} ({remote_config['model_2']})"
                )
                task_start_times[id(remote_task_2)] = time.perf_counter()
                tasks.append(remote_task_2)
                
            except Exception as e:
                logger.error(f"Failed to create remote agents: {e}")
                
            if not tasks:
                raise Exception("No generation agents available")
    
            race_duration = 0.0
            
            winner_text = None
            winner_source = None
            failed_attempts = []
            finished_alternatives = [] # To store successes that weren't the winner (if any)
            
            # Race loop
            should_break_race = False
            
            while tasks:
                # Wait for the next one to complete
                elapsed = time.perf_counter() - race_start
                remaining = 60.0 - elapsed
                
                if remaining <= 0:
                    logger.warning("Generation race timed out after 60s")
                    break
                    
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=remaining)
                
                if not done:
                     # Timeout hit during wait
                     logger.warning("Generation race timed out during wait")
                     break
                
                for task in done:
                    try:
                        result = await task
                        if not winner_text:
                            # We have our first winner!
                            winner_text = result["output"]
                            winner_source = result["source"]
                            winner_duration = time.perf_counter() - task_start_times[id(task)]
                            race_duration = time.perf_counter() - race_start
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
                        
                        # Detect Rate Limit or Failure for Primary
                        error_str = str(e).lower()
                        is_rate_limit = "429" in error_str or "rate limit" in error_str
                        
                        if self.current_provider_name == "groq":
                            # For Groq (Primary), failover on most errors to try OpenRouter
                            # We treat it as a rate limit/downtime to trigger the switch
                            logfire.warning(f"Groq failed ({e}), failover to OpenRouter")
                            self.provider_service.report_rate_limit("groq")
                            # Do NOT break the race immediately. Let the Local model (and others) continue.
                            # If Local succeeds, we win.
                            # If Local fails, we'll see the provider changed (via report_rate_limit) 
                            # and trigger a retry with the new provider (OpenRouter) naturally.
                            # should_break_race = True
                        
                        elif is_rate_limit and self.current_provider_name == "openrouter":
                            # For OpenRouter (Secondary), only report if it's a rate limit
                            self.provider_service.report_rate_limit("openrouter")
                
                if winner_text or should_break_race:
                    break
                else:
                    tasks = list(pending)
            
            # End of race loop for this attempt
            
            if winner_text:
                 # Success! Return result
                 # Handle Alternatives
                 
                 alt_id = str(uuid.uuid4())
                 current_alts = []
                 for alt in finished_alternatives:
                      current_alts.append(alt)
                 for fail in failed_attempts:
                     if not any(a["source"] == fail["source"] for a in current_alts):
                         current_alts.append({
                             "text": f"Generation failed: {fail['error']}",
                             "source": fail["source"],
                             "status": "failed"
                         })
                         
                 self.alternatives_store[alt_id] = {
                     "status": "pending" if pending else "completed",
                     "alternatives": current_alts
                 }
                 
                 if pending:
                     task = asyncio.create_task(self._process_alternatives(pending, alt_id, task_start_times))
                     self.background_tasks.add(task)
                     task.add_done_callback(self.background_tasks.discard)
                     
                 return winner_text, winner_source, alt_id
            
            # If no winner, checks for retry condition
            # Check if provider has changed during the race (due to reporting rate limit)
            new_config = self.provider_service.get_provider_config()
            if new_config["name"] != self.current_provider_name and attempt <= max_retries:
                logger.warning(f"Provider failover triggered (from {self.current_provider_name} to {new_config['name']}). Retrying generation...")
                logfire.info("Retrying with new provider", attempts_made=attempt)
                
                # Cancel pending tasks from this failed attempt to free resources and avoid hanging
                for t in tasks:
                    t.cancel()
                    
                continue # Retry loop
            
            # If we are here, we failed and strictly no retry condition met or max retries exceeded
            error_summary = "; ".join([f"{f['source']}: {f['error']}" for f in failed_attempts])
            logfire.error("All models failed", failures=failed_attempts)
            if attempt > max_retries:
                 raise Exception(f"All models failed after {attempt} attempts. Errors: {error_summary}")
            else:
                 raise Exception(f"All models failed. Errors: {error_summary}")

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
