"""
Application Management Unit Tests

This module tests the core business logic for managing job applications.
It includes tests for updating application statuses, modifying job descriptions,
and ensuring that users can only modify their own data (unauthorized access
prevention).
"""

import pytest
from unittest.mock import MagicMock
from app.api.routes.application import update_application
from app.api.validation.schemas import UpdateApplicationRequest
from database_pkg.models import Application, JobDescription, ApplicationStatus
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_update_application_logic():
    # Mock dependencies
    session = MagicMock()
    current_user = MagicMock(id=1)

    # Mock application and job description
    mock_app = Application(
        id=1,
        user_id=1,
        status=ApplicationStatus.APPLIED,
        cover_letter_final={"body": "old"},
    )
    mock_job = JobDescription(id=1, job_title="Old Title", company="Old Co")

    # Mock session.exec
    session.exec.return_value.first.return_value = (mock_app, mock_job)

    request = UpdateApplicationRequest(
        job_title="New Title", notes="New Note", status="interview"
    )

    result = await update_application(
        application_id=1, request=request, session=session, current_user=current_user
    )

    assert result["success"] is True
    assert mock_job.job_title == "New Title"
    assert mock_app.notes == "New Note"
    assert mock_app.status == ApplicationStatus.INTERVIEW
    assert session.commit.called


@pytest.mark.asyncio
async def test_update_application_unauthorized():
    session = MagicMock()
    current_user = MagicMock(id=2)  # Different user

    # Mock session.exec to return None (since we filter by user_id in the query)
    session.exec.return_value.first.return_value = None

    request = UpdateApplicationRequest(notes="test")

    with pytest.raises(HTTPException) as exc:
        await update_application(
            application_id=1,
            request=request,
            session=session,
            current_user=current_user,
        )

    assert exc.value.status_code == 404
