import pytest
from unittest.mock import AsyncMock, patch
from app.api.validation.schemas import CoverLetterRequest, JobDescription

@pytest.mark.asyncio
async def test_job_id_injection_regression():
    """
    Regression test to ensure job_id is always injected into the 
    request data before starting the Temporal workflow.
    """
    from app.api.routes.cover_letter import generate_cover_letter
    
    # 1. Prepare request
    request = CoverLetterRequest(
        job_description=JobDescription(
            title="SDE", company="Co", description="D", requirements=[], url="U"
        )
    )

    # 2. Mock and execute
    mock_client = AsyncMock()
    with patch("app.api.routes.cover_letter.get_temporal_client", return_value=mock_client):
        result = await generate_cover_letter(request)
        
        # 3. Verify
        job_id = result["job_id"]
        args, _ = mock_client.start_workflow.call_args
        workflow_input = args[1]
        
        assert "job_id" in workflow_input, "job_id missing from workflow input!"
        assert workflow_input["job_id"] == job_id, "job_id mismatch in workflow input!"
