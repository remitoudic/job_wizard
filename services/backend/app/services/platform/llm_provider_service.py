import time
from typing import Dict, Any, Literal
from app.core.config import settings
import logfire

ProviderType = Literal["openrouter", "groq"]


class LLMProviderService:
    """
    Manages LLM providers and handles failover when rate limits are reached.
    Singleton pattern can be enforced by usage.
    """

    def __init__(self):
        self._groq_rate_limit_until = 0.0
        self._active_provider: ProviderType = "groq"

        # Rate limit cooldown in seconds
        self._default_cooldown = 3600

    def get_active_provider(self) -> ProviderType:
        """Returns the current active provider based on rate limit status."""
        current_time = time.time()

        if self._active_provider == "groq":
            if current_time < self._groq_rate_limit_until:
                # Groq is rate limited, switch to OpenRouter
                logfire.info("Groq is rate limited, using OpenRouter")
                return "openrouter"

        # If we were in openrouter mode, check if we can switch back to Groq (Primary)
        if self._active_provider == "openrouter":
            if current_time >= self._groq_rate_limit_until:
                # Cooldown expired, switch back to Groq
                logfire.info("Groq cooldown expired, switching back to primary")
                return "groq"
            return "openrouter"

        return "groq"

    def report_rate_limit(self, provider: ProviderType, reset_time: float = None):
        """
        Report that a provider has hit a rate limit.
        """
        with logfire.span("Provider Rate Limit: {provider}", provider=provider):
            current_time = time.time()

            if provider == "groq":
                if reset_time:
                    self._groq_rate_limit_until = reset_time
                else:
                    self._groq_rate_limit_until = current_time + self._default_cooldown

                self._active_provider = "openrouter"
                logfire.warning(
                    "Rate limit reported for Groq",
                    active_provider_now="openrouter",
                    downtime_seconds=self._groq_rate_limit_until - current_time,
                )
            elif provider == "openrouter":
                # If OpenRouter also fails, we just log it.
                # We rely on Groq being available after cooldown.
                logfire.error("OpenRouter (Secondary) also reported rate limit!")

    def get_provider_config(self) -> Dict[str, Any]:
        """
        Get configuration for the currently active provider.
        Returns a dict with:
        - base_url
        - api_key
        - model_1
        - model_2
        """
        provider = self.get_active_provider()

        if provider == "groq":
            return {
                "name": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.GROQ_API_KEY,
                "model_1": settings.GROQ_MODEL_1,
                "model_2": settings.GROQ_MODEL_2,
            }
        else:  # openrouter
            return {
                "name": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": settings.OPENROUTER_API_KEY,
                "model_1": settings.OPENROUTER_MODEL,
                "model_2": settings.OPENROUTER_MODEL_2,
            }

    def get_nvidia_config(self) -> Dict[str, Any] | None:
        """
        Get NVIDIA NIM config if API key is present.
        NVIDIA is an independent race participant, not a failover target.
        Returns None if NVIDIA is not configured.
        """
        if not settings.NVIDIA_API_KEY:
            return None
        return {
            "name": "nvidia",
            "base_url": "https://integrate.api.nvidia.com/v1",
            "api_key": settings.NVIDIA_API_KEY,
            "model_1": settings.NVIDIA_MODEL_1,
            "model_2": settings.NVIDIA_MODEL_2,
        }


# Global singleton instance
llm_provider_service = LLMProviderService()
