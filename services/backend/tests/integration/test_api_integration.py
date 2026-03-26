from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
from app.api.routes.cover_letter import llm_service  # noqa: E402

def test_generate_cover_letter_endpoint():
    """
    Integration test for the /generate-cover-letter endpoint.
    Verifies that the API accepts the payload and triggers the LLM service.
    """
    payload = {
        "job_description": {
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "description": "We are looking for an expert in FastAPI and Python.",
            "requirements": ["Python", "FastAPI", "Docker", "AWS"],
            "url": "https://example.com/job"
        },
        "user_name": "Integration Tester",
        "user_skills": "Python, FastAPI, Docker, Kubernetes, CI/CD",
        "context_text": "I have 5 years of experience building scalable APIs."
    }
    
    # Note: The endpoint prefix might be /api/cover_letter or just /cover_letter depending on main.py router inclusion
    # Assuming /api/cover-letter based on common patterns, but will try direct first if router tags are used
    # checking config.py: API_V1_STR = "/api"
    # and knowing routes usually included with prefix.
    # We'll use the proper full path if we can check main.py, but assuming:
    # /api/cover-letter/generate-cover-letter
    
    try:
        response = client.post("/api/generate-cover-letter", json=payload)
        
        # We assert 200 OK. 
        # Even if models fail (500), we want to see what happens.
        # Ideally, we want a success.
        
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cover_letter" in data
        assert len(data["cover_letter"]) > 0
        assert data["job_title"] == "Senior Python Developer"
        assert data["company"] == "TechCorp"
        
        print("\n✅ API Integration Test Passed!")
        print(f"   Generated letter length: {len(data['cover_letter'])}")
        print(f"   Source: {data.get('source', 'unknown')}")
        
    finally:
        # Cancel any background tasks (e.g. slow local models processing alternatives)
        # to prevent test from hanging
        if hasattr(llm_service, "cleanup"):
            llm_service.cleanup()
