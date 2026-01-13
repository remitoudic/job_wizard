import pydantic_ai.models
print("dir(models):", dir(pydantic_ai.models))
try:
    from pydantic_ai.models.ollama import OllamaModel
    print("OllamaModel found in .models.ollama")
except ImportError:
    print("OllamaModel NOT found in .models.ollama")
