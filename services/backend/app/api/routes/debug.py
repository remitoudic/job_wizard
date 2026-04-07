from fastapi import APIRouter, Depends
from typing import Dict, Any
import httpx
import ollama
import cloudinary
import cloudinary.api
import time
from sqlalchemy import text
import logfire

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.core.pubsub import pubsub_manager

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/health")
async def debug_health(
    current_user: CurrentUser,
    session: SessionDep
) -> Dict[str, Any]:
    """
    Diagnostic endpoint to check connectivity with all external services.
    Only accessible to authenticated users.
    """
    results = {}
    
    # 1. Database & PubSub Health
    try:
        start_time = time.perf_counter()
        session.exec(text("SELECT 1")).first()
        db_latency = time.perf_counter() - start_time
        
        pubsub_status = "active" if pubsub_manager._running and pubsub_manager._task and not pubsub_manager._task.done() else "down"
        
        results["database"] = {
            "status": "ok",
            "latency_ms": round(db_latency * 1000, 2),
            "pubsub": pubsub_status
        }
    except Exception as e:
        results["database"] = {"status": "error", "message": str(e)}

    # 2. Ollama Connectivity
    try:
        start_time = time.perf_counter()
        client = ollama.AsyncClient(host=settings.OLLAMA_HOST)
        models_resp = await client.list()
        ollama_latency = time.perf_counter() - start_time
        
        # Check if the configured model is pre-pulled
        available_models = [m["name"] for m in models_resp.get("models", [])]
        model_ready = settings.OLLAMA_MODEL in available_models or f"{settings.OLLAMA_MODEL}:latest" in available_models
        
        results["ollama"] = {
            "status": "ok",
            "latency_ms": round(ollama_latency * 1000, 2),
            "host": settings.OLLAMA_HOST,
            "configured_model": settings.OLLAMA_MODEL,
            "model_ready": model_ready,
            "available_models_count": len(available_models)
        }
    except Exception as e:
        results["ollama"] = {"status": "error", "message": str(e), "host": settings.OLLAMA_HOST}

    # 3. LLM Provider Status (Cloud)
    results["providers"] = {}
    
    async with httpx.AsyncClient(timeout=5.0) as http_client:
        # Groq Check
        if settings.GROQ_API_KEY:
            try:
                start_time = time.perf_counter()
                resp = await http_client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
                )
                groq_latency = time.perf_counter() - start_time
                results["providers"]["groq"] = {
                    "status": "ok" if resp.status_code == 200 else "error",
                    "status_code": resp.status_code,
                    "latency_ms": round(groq_latency * 1000, 2)
                }
            except Exception as e:
                results["providers"]["groq"] = {"status": "error", "message": str(e)}
        else:
            results["providers"]["groq"] = {"status": "skipped", "message": "No API key configured"}

        # OpenRouter Check
        if settings.OPENROUTER_API_KEY:
            try:
                start_time = time.perf_counter()
                resp = await http_client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
                )
                or_latency = time.perf_counter() - start_time
                results["providers"]["openrouter"] = {
                    "status": "ok" if resp.status_code == 200 else "error",
                    "status_code": resp.status_code,
                    "latency_ms": round(or_latency * 1000, 2)
                }
            except Exception as e:
                results["providers"]["openrouter"] = {"status": "error", "message": str(e)}
        else:
            results["providers"]["openrouter"] = {"status": "skipped", "message": "No API key configured"}

    # 4. Cloudinary Connectivity
    if settings.CLOUDINARY_URL:
        try:
            start_time = time.perf_counter()
            # cloudinary.api.ping() is a lightweight way to check connectivity
            cloudinary.api.ping()
            cloudinary_latency = time.perf_counter() - start_time
            results["cloudinary"] = {
                "status": "ok",
                "latency_ms": round(cloudinary_latency * 1000, 2)
            }
        except Exception as e:
            results["cloudinary"] = {"status": "error", "message": str(e)}
    else:
        results["cloudinary"] = {"status": "skipped", "message": "No Cloudinary URL configured"}

    # 5. LlamaCloud (CV Parsing) Connectivity
    if settings.LLAMA_CLOUD_API_KEY:
        try:
            start_time = time.perf_counter()
            # Simple reachability check to LlamaIndex Cloud API
            async with httpx.AsyncClient(timeout=5.0) as http_client:
                resp = await http_client.get(
                    "https://api.cloud.llamaindex.ai/api/health",
                )
                llama_latency = time.perf_counter() - start_time
                results["llamacloud"] = {
                    "status": "ok" if resp.status_code == 200 else "error",
                    "status_code": resp.status_code,
                    "latency_ms": round(llama_latency * 1000, 2)
                }
        except Exception as e:
            results["llamacloud"] = {"status": "error", "message": str(e)}
    else:
        results["llamacloud"] = {"status": "skipped", "message": "No LlamaCloud API key configured"}

    logfire.info("Debug health check performed", results=results)
    return results
