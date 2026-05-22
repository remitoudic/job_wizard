from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


def test_generate_cover_letter_api_with_custom_instructions():
    # Mock the workflow to avoid actual execution
    from unittest.mock import AsyncMock

    with patch(
        "app.api.routes.cover_letter.get_temporal_client", new_callable=AsyncMock
    ) as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

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
        assert "job_id" in data

        # Verify the workflow was called with custom_instructions
        mock_client.start_workflow.assert_called_once()
        call_args, call_kwargs = mock_client.start_workflow.call_args
        workflow_data = call_args[1] if len(call_args) > 1 else call_kwargs.get("arg")
        if workflow_data is None:
            # Depending on how it's called, check the kwargs
            workflow_data = call_args[1]
        assert workflow_data["custom_instructions"] == "Make it funny"
