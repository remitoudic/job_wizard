import asyncio
import time
import logging
import uuid
from typing import Optional, Dict, Any

from app.services.platform.agents import create_writing_agent, create_extraction_agent
from app.core.config import settings
from app.core.pubsub import pubsub_manager
import logfire
from pydantic import ValidationError
from app.core.logging.prompt_audit import prompt_audit_logger
from app.services.platform.llm_provider_service import llm_provider_service

class LLMService:
    """Service for generating cover letters using Pydantic AI Agents"""
    
    def __init__(self):
        # Configuration
        self.ollama_host = settings.OLLAMA_HOST
        self.ollama_model_name = settings.OLLAMA_MODEL
        
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

    @staticmethod
    def clean_model_output(text: str) -> str:
        """
        Heuristically clean the model output to remove headers, addresses, 
        and signatures that the model might have hallucinated.
        Also sanitizes Unicode characters that cause rendering issues in PDFs.
        """
        import re
        
        # --- Phase 0: Sanitize problematic Unicode characters ---
        # LLMs frequently emit special hyphens, smart quotes, and zero-width
        # characters that ReportLab's built-in fonts can't render (black boxes).
        from app.services.cover_letter.templates.base import BaseTemplate
        text = BaseTemplate.sanitize_text(text)
        
        lines = text.strip().split('\n')
        
        # 1. Strip Header Junk (Addresses, Dates, Names at the top)
        # Strategy: Skip lines until we find a likely Salutation or the Body start
        # Heuristics for lines to skip:
        # - Short lines with digits (dates, phone numbers)
        # - Lines with email patterns
        # - Lines that look like names (short, capitalized)
        # - "Subject:" lines
        
        start_index = 0
        # salutations (handle trailing colon or comma)
        salutation_regex = r"^(Dear|Hi|Hello|Sehr|Hallo|Guten|Madame|Monsieur|Bonjour|Estimado|Estimada|Hola|A quien corresponda)\b"
        
        for i, line in enumerate(lines[:15]): # Only check first 15 lines
            line_str = line.strip()
            if not line_str:
                continue
                
            # Stop if we hit a Salutation
            if re.match(salutation_regex, line_str, re.IGNORECASE):
                start_index = i
                break
            
            # Stop if we hit a paragraph that looks like a body (long enough)
            if len(line_str) > 100:
                start_index = i
                break
                
            # Otherwise, assume it's header junk and skip
            # (aggressive, but tailored for the prompt 'OUTPUT BODY ONLY')
            if i == 14:
                start_index = 0

        # If we found a specific start point, use it. 
        if start_index > 0:
             lines = lines[start_index:]
             
        # 2. Strip Footer/Signature
        joined_text = "\n".join(lines).strip()
        
        # Regex to find signature block and removing it
        # Includes English and German variants
        sig_pattern = re.compile(
            r"(Sincerely|Best regards|Yours truly|Respectfully|Kind regards|Mit freundlichen Grüßen|Beste Grüße|Herzliche Grüße|Viele Grüße|Cordialement|Bien à vous|Sincères salutations|Je vous prie d'agréer|Atentamente|Cordialmente|Un cordial saludo|Suyo sinceramente)[\s,]*[\s\S]*$", 
            re.IGNORECASE
        )
        match = sig_pattern.search(joined_text)
        if match:
             joined_text = joined_text[:match.start()].strip()
             
        return joined_text
    
    async def extract_contact_info(self, text: str) -> Dict[str, Any]:
        """
        Extract contact info using Pydantic AI Agent
        """
        with logfire.span("Contact Info Extraction"):
            try:
                # Agent.run is async
                logfire.info("Starting contact extraction")
                result = await self.extractor.run(text)
                data = result.output.model_dump()
                
                # Capture usage
                usage = result.usage()
                logfire.info("Extraction usage", tokens=usage.total_tokens)
                
                # Robustness: Backfill first/surname from name if missing
                full_name = data.get("name", "").strip()
                if full_name:
                    if not data.get("first_name"):
                        parts = full_name.split(" ")
                        if parts:
                            data["first_name"] = parts[0]
                    
                    if not data.get("surname"):
                        parts = full_name.split(" ")
                        if len(parts) > 1:
                            # Join all remaining parts as surname
                            data["surname"] = " ".join(parts[1:])
                
                return data
            except ValidationError as e:
                logfire.error("Extraction validation failed", error=str(e))
                prompt_audit_logger.log_failure(
                    context="Contact Extraction (Validation)",
                    raw_output="N/A (Managed by Pydantic AI)", # Hard to get raw string from managed agent without refactor
                    error=str(e),
                    model_name=self.ollama_model_name
                )
                return {}
            except Exception as e:
                logfire.error("Extraction failed", error=str(e))
                prompt_audit_logger.log_failure(
                    context="Contact Extraction (Generic)",
                    raw_output="N/A (Managed by Pydantic AI)",
                    error=str(e),
                    model_name=self.ollama_model_name
                )
                return {}

    async def generate_cover_letter(
        self,
        job_description: str,
        job_title: str,
        company: str,
        requirements: list[str],
        job_id: str, # Required for tracking
        user_name: str = "",
        user_skills: str = "",
        context_text: Optional[str] = None,
        custom_instructions: Optional[str] = None,
        language: str = "english",
    ) -> tuple[str, str, str]:
        """
        Generate cover letter with race mode (Local vs Remote)
        """
        logfire.info("Generate Cover Letter start", job_id=job_id)
        logger = logging.getLogger("app.services.cover_letter.llm_service")
        
        # Build optimized prompt (concise for speed)
        req_list = ', '.join(requirements[:5]) if requirements else 'See description'
        
        # Language-specific instructions
        is_german = language.lower() == "german"
        is_french = language.lower() == "french"
        is_spanish = language.lower() == "spanish"

        if is_german:
            lang_block = """
LANGUAGE: Write the ENTIRE letter in German (Deutsch).
- Use formal German throughout.
- Salutation: "Sehr geehrte Damen und Herren," (or personalized if recipient name is known).
- Do NOT write in English. Every word must be in German.
- Tone: Formal, structured, professional (Bewerbungsschreiben standard)."""
            STANDARD_SIGNATURE = "\n\nMit freundlichen Grüßen\n\n[Ihr Name]"
            salutation_hint = '"Sehr geehrte/r [Name]," (or "Sehr geehrte Damen und Herren,")'
        elif is_french:
            lang_block = """
LANGUAGE: Write the ENTIRE letter in French (Français).
- Use formal French ("vouvoiement") throughout.
- Salutation: "Madame, Monsieur,".
- Do NOT write in English. Every word must be in French.
- Structure: Follow the "Vous, Moi, Nous" standard for French cover letters.
- Tone: Professional, motivated, and formal (Lettre de Motivation)."""
            STANDARD_SIGNATURE = "\n\nCordialement,\n\n[Votre Nom]"
            salutation_hint = '"Madame, Monsieur,"'
        elif is_spanish:
            lang_block = """
LANGUAGE: Write the ENTIRE letter in Spanish (Español).
- Use formal Spanish throughout.
- Salutation: "A quien corresponda,".
- Do NOT write in English. Every word must be in Spanish.
- Tone: Professional, formal, and persuasive (Carta de Presentación standard)."""
            STANDARD_SIGNATURE = "\n\nUn cordial saludo,\n\n[Su nombre]"
            salutation_hint = '"A quien corresponda,"'
        else:
            lang_block = "\nLANGUAGE: Write in British English."
            STANDARD_SIGNATURE = "\n\nSincerely,\n\n[Your Name]"
            salutation_hint = '"Dear Hiring Manager," (or similar)'

        # Shared base instructions
        base_prompt = f"""Write a professional cover letter applying to {company} as {job_title}.
{lang_block}

IMPORTANT INSTRUCTIONS:
1. OUTPUT BODY ONLY. Do NOT include a header, address block, date, or contact info.
2. Start directly with {salutation_hint}.
3. Do NOT include a signature. I will add this programmatically.
4. Do NOT include your name or any placeholders like "[Your Name]" or "[Date]".
5. Keep the letter between 200 and 400 words.
6. Maintain a formal, business-appropriate tone.

Key requirements: {req_list}
Candidate skills: {user_skills}

CUSTOM USER GUIDANCE:
{custom_instructions if custom_instructions else 'None provided.'}
"""
        # Remote prompt gets more context
        prompt = base_prompt
        if context_text:
            prompt += f"\nCandidate background:\n{context_text[:1500]}"

        # Local prompt gets reduced context
        local_prompt = base_prompt
        if context_text:
            local_context = context_text[:500]
            local_prompt += f"\nCandidate background:\n{local_context}"

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
            
            # Notify: Race started
            await pubsub_manager.notify({
                "job_id": job_id,
                "status": "generating",
                "message": f"Starting generation race using {self.current_provider_name}...",
                "provider": self.current_provider_name
            })
            
            race_start = time.perf_counter()
            tasks = []
            task_start_times = {}
            
            # Helper to wrap agent run with source info
            async def run_agent(agent, p, name):
                with logfire.span("Agent Generation: {source}", source=name) as agent_span:
                    res = await agent.run(p)
                    
                    # Capture token usage
                    usage = res.usage()
                    agent_span.set_attribute("request_tokens", usage.request_tokens)
                    agent_span.set_attribute("response_tokens", usage.response_tokens)
                    agent_span.set_attribute("total_tokens", usage.total_tokens)
                    
                    # Post-process: Aggressive cleaning using heuristic cleaner
                    clean_text = LLMService.clean_model_output(res.output)
                    
                    # Append standard signature
                    final_text = f"{clean_text}{STANDARD_SIGNATURE}"
                    
                    # Replace name placeholder
                    display_name = user_name if user_name else "[Your Name]"
                    final_text = final_text.replace("[Your Name]", display_name).replace("[Ihr Name]", display_name).replace("[Votre Nom]", display_name).replace("[Su nombre]", display_name)
                    
                    usage_dict = {
                        "request_tokens": usage.request_tokens,
                        "response_tokens": usage.response_tokens,
                        "total_tokens": usage.total_tokens
                    } if usage else None
                    
                    return {"output": final_text, "source": name, "usage": usage_dict}

            # Task 1: Logic to prefer Local but Failover if Busy
            
            # Application-level throttling for Local Ollama
            # We allow 2 concurrent requests to match OLLAMA_NUM_PARALLEL in docker-compose
            if not hasattr(self, "ollama_semaphore"):
                self.ollama_semaphore = asyncio.Semaphore(2)

            # Check if local is busy
            if self.ollama_semaphore.locked():
                 # Local is busy (2 slots taken).
                 # User requested IMMEDIATE failover to cloud.
                 logfire.warn("Local model busy (2/2 active). Failover to cloud immediately.")
                 logger.warning("Local model busy. Skipping local generation task.")
                 
                 # We simply don't start the local task. 
                 # The code below will ensure at least one remote task is started.
                 # If no remote is configured, we must raise an error here or let the empty task list raise it.
                 
                 # Check if we have remote config
                 remote_config = self.provider_service.get_provider_config()
                 if not remote_config or not remote_config.get("api_key"):
                     raise Exception("System is currently busy (Local capacity full) and no Cloud provider is configured for failover.")
                     
            else:
                # Local slot available, start local task wrapped in semaphore
                async def run_local_with_semaphore():
                    async with self.ollama_semaphore:
                        return await run_agent(self.local_writer, local_prompt, f"Ollama ({self.ollama_model_name})")

                local_task = asyncio.create_task(
                    run_local_with_semaphore(), 
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
            
            # NVIDIA participant — always races if API key is configured
            try:
                nvidia_config = self.provider_service.get_nvidia_config()
                if nvidia_config:
                    nvidia_writer = create_writing_agent(
                        model_name=nvidia_config["model_1"],
                        is_remote=True,
                        provider_config=nvidia_config
                    )
                    nvidia_task = asyncio.create_task(
                        run_agent(nvidia_writer, prompt, f"Nvidia ({nvidia_config['model_1']})"),
                        name=f"Nvidia ({nvidia_config['model_1']})"
                    )
                    task_start_times[id(nvidia_task)] = time.perf_counter()
                    tasks.append(nvidia_task)
                    logger.info(f"NVIDIA participant added: {nvidia_config['model_1']}")
            except Exception as e:
                logger.error(f"Failed to create NVIDIA agent: {e}")

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
                                failed_attempts=len(failed_attempts),
                                usage=result.get("usage")
                            )
                            logger.info(f"Race won by {winner_source} in {winner_duration:.2f}s")
                        else:
                            # Already have a winner, this is an alternative
                            finished_alternatives.append({
                                "text": result["output"],
                                "source": result["source"],
                                "status": "completed",
                                "usage": result.get("usage")
                            })
                            
                    except Exception as e:
                        failed_source = task.get_name()
                        failed_attempts.append({"source": failed_source, "error": str(e)})
                        logger.warning(f"Model failed: {failed_source} - {e}")
                        logfire.warning("Model failed", source=failed_source, error=str(e))
                        
                        # Classify the error to decide if provider failover is needed
                        error_str = str(e).lower()
                        is_rate_limit = "429" in error_str or "rate limit" in error_str
                        is_server_error = "502" in error_str or "503" in error_str or "server error" in error_str
                        is_model_error = (
                            "404" in error_str 
                            or "not found" in error_str 
                            or "deprecated" in error_str 
                            or "invalid model" in error_str
                            or "does not exist" in error_str
                        )
                        is_auth_error = "401" in error_str or "unauthorized" in error_str or "403" in error_str
                         
                        # Only trigger provider failover for rate limits or server-wide outages.
                        # Model-specific errors (deprecated, not found) should NOT poison the
                        # entire provider — other models on the same provider may still work.
                        if is_rate_limit or is_server_error or is_auth_error:
                            if self.current_provider_name == "groq":
                                logfire.warning(f"Groq provider issue ({e}), failover to OpenRouter")
                                self.provider_service.report_rate_limit("groq")
                            elif self.current_provider_name == "openrouter":
                                self.provider_service.report_rate_limit("openrouter")
                        elif is_model_error:
                            logfire.warning(
                                "Model-specific error (no provider failover)", 
                                source=failed_source, 
                                error=str(e)
                            )
                
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
                     # Notify: Primary ready, processing alternatives
                     await pubsub_manager.notify({
                         "job_id": job_id,
                         "status": "partial",
                         "message": "Primary letter ready. Processing alternatives...",
                         "winner": winner_source,
                         "text": winner_text,
                         "source": winner_source,
                         "alternative_id": alt_id
                     })
                     
                     task = asyncio.create_task(self._process_alternatives(pending, alt_id, job_id, task_start_times))
                     self.background_tasks.add(task)
                     task.add_done_callback(self.background_tasks.discard)
                     
                 else:
                    # Notify: All completed immediately
                    await pubsub_manager.notify({
                        "job_id": job_id,
                        "status": "completed",
                        "message": "Generation complete!",
                        "winner": winner_source,
                        "text": winner_text,
                        "source": winner_source,
                        "alternative_id": alt_id,
                        "alternatives": current_alts
                    })
                     
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

    async def _process_alternatives(self, pending_tasks, alt_id: str, job_id: str, task_start_times: dict):
        """Handle the slower tasks incrementally"""
        logger = logging.getLogger("app.services.cover_letter.llm_service")
        
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
                            "status": "completed",
                            "usage": result.get("usage")
                        }
                        current_alternatives.append(alt)
                        logfire.info(
                            "Alternative completed", 
                            id=alt_id, 
                            source=result["source"],
                            duration_seconds=round(task_duration, 2),
                            usage=result.get("usage")
                        )
                        logger.info(f"Alternative completed: {result['source']} in {task_duration:.2f}s")
                        
                        # Notify frontend that an alternative is ready
                        await pubsub_manager.notify({
                            "job_id": job_id,
                            "status": "alternative_ready",
                            "text": alt["text"],
                            "source": alt["source"],
                            "alternatives": current_alternatives
                        })
                    except Exception as e:
                        task_duration = time.perf_counter() - task_start_times.get(id(task), 0)
                        alt = {
                            "text": f"Generation failed: {str(e)}",
                            "source": task.get_name(),
                            "status": "failed"
                        }
                        current_alternatives.append(alt)
                        logger.error(f"Alternative failed: {task.get_name()} - {e}")
                        
                        # Notify frontend of failure
                        await pubsub_manager.notify({
                            "job_id": job_id,
                            "status": "alternative_ready",
                            "text": alt["text"],
                            "source": alt["source"],
                            "alternatives": current_alternatives
                        })
                
                # Update store incrementally
                self.alternatives_store[alt_id] = {
                    "status": "pending" if pending else "completed",
                    "alternatives": current_alternatives
                }
                
                # Continue with remaining
                tasks = list(pending)
            
            if not tasks:
                # Final Notify
                await pubsub_manager.notify({
                    "job_id": job_id,
                    "status": "completed",
                    "message": "All alternatives generated.",
                    "alternatives": current_alternatives
                })
            
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
