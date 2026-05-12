"""
NVIDIA API Model Capabilities Tester

This script queries the NVIDIA NIM API to retrieve a list of all currently supported models.
It was created to debug why certain model identifiers (like 'nvidia/nemotron-3-content-safety') 
were failing during the cover letter generation race. 

Why it makes sense to test it like this:
Instead of debugging blindly through the backend application logs (which can be noisy 
and require restarting services to test new configurations), this script directly tests 
the external API dependency in isolation. By fetching the raw source of truth from the 
NVIDIA API endpoint, we can immediately verify if a model string exists, if the API key 
has access to it, and what alternatives are available (like 'mistralai/mistral-large-3-675b-instruct-2512').
"""
import os
import httpx

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
if not NVIDIA_API_KEY:
    with open(".env/.env.production") as f:
        for line in f:
            if line.startswith("NVIDIA_API_KEY="):
                NVIDIA_API_KEY = line.strip().split("=")[1]
                break

headers = {"Authorization": f"Bearer {NVIDIA_API_KEY}"}
response = httpx.get("https://integrate.api.nvidia.com/v1/models", headers=headers)
models = response.json().get("data", [])
for m in models:
    print(m["id"])
