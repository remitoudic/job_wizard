from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


def test_generate_cover_letter_api_with_custom_instructions():
    # Mock the LLM service to avoid actual generation
    with patch("app.api.routes.cover_letter.llm_service") as mock_service:
        # Setup mock return value
        mock_service.generate_cover_letter = AsyncMock(
            return_value=("Cover Letter Content", "MockAI", "alt-id-123")
        )

        payload = {
            "job_description": {
                "title": "Dev",
                "company": "TestCorp",
                "description": "Code stuff",
                "requirements": ["Python"],
                "url": "http://test.com",
            },
            "user_name": " Tester",
            "custom_instructions": "Make it funny",
        }

        response = client.post("/api/generate-cover-letter", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["cover_letter"] == "Cover Letter Content"

        # Verify the service was called with custom_instructions
        mock_service.generate_cover_letter.assert_called_once()
        call_kwargs = mock_service.generate_cover_letter.call_args[1]
        assert call_kwargs["custom_instructions"] == "Make it funny"
