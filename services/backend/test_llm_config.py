from app.services.platform.llm_provider_service import llm_provider_service

config = llm_provider_service.get_provider_config()
print("Base URL:", config.get("base_url"))
print(
    "API Key type:", type(config.get("api_key")), "value:", repr(config.get("api_key"))
)
