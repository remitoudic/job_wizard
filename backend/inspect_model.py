from pydantic_ai.models.openai import OpenAIModel
import inspect

try:
    print("Signature:", inspect.signature(OpenAIModel.__init__))
except Exception as e:
    print("Error inspecting:", e)
    print("mro:", OpenAIModel.mro())
