import pytest
from unittest.mock import MagicMock
from app.api.routes.application import export_applications_excel
from database_pkg.models import Application, JobDescription, ApplicationStatus
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_export_applications_excel_sanitizes_control_characters():
    # Mock database session
    session = MagicMock()
    current_user = MagicMock(id=1)

    # Application and JobDescription containing illegal XML control characters
    mock_app = Application(
        id=1,
        user_id=1,
        status=ApplicationStatus.APPLIED,
        notes="Some notes with \x1a control character.",
        cover_letter_final={"body": "Hello\x00World!"},
        created_at=datetime.now(timezone.utc),
    )
    mock_job = JobDescription(
        id=1,
        job_title="Software\x07Engineer",
        company="Tech\x0bCorp",
        url="https://example.com/job",
        requirements=["Python\x1f", "FastAPI"],
        full_description="Job with \x02 control character.",
    )

    # Mock query results
    session.exec.return_value.all.return_value = [(mock_app, mock_job)]

    # Call the export route function
    response = await export_applications_excel(
        session=session,
        current_user=current_user,
        format="xlsx",
    )

    # Assert response is a StreamingResponse and does not crash
    assert response is not None
    assert (
        response.media_type
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
