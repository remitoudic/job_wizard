"""Unit tests for the check-duplicate-application endpoint logic."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from database_pkg.models import Application, ApplicationStatus, JobDescription
from fastapi import HTTPException
from sqlalchemy.sql import Select

from app.api.routes.application import check_duplicate_application


def _make_app_and_job(
    app_id: int = 1,
    job_title: str = "Engineer",
    company: str = "Acme",
    status: ApplicationStatus = ApplicationStatus.APPLIED,
    cover_body: str | None = "Dear...",
    notes: str | None = None,
    created: datetime | None = None,
) -> tuple[Application, JobDescription]:
    if created is None:
        created = datetime(2025, 1, 1)
    job = JobDescription(
        id=1,
        url="https://example.com/job/123",
        job_title=job_title,
        company=company,
        full_description="desc",
        requirements=["Python"],
        source="Manual",
    )
    app = Application(
        id=app_id,
        user_id=1,
        job_description_id=job.id,
        status=status,
        notes=notes,
        cover_letter_final={"model": "test", "timestamp": "2025", "body": cover_body},
        created_at=created,
    )
    return app, job


@pytest.mark.asyncio
class TestCheckDuplicateNoMatch:
    async def test_no_apps_exist(self):
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        result = await check_duplicate_application(
            job_url="https://example.com/job/123",
            session=session,
            current_user=MagicMock(id=1),
        )
        assert result == {"is_duplicate": False, "existing_application": None}

    async def test_url_not_found(self):
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        result = await check_duplicate_application(
            job_url="https://other.com/other",
            session=session,
            current_user=MagicMock(id=1),
        )
        assert result == {"is_duplicate": False, "existing_application": None}


@pytest.mark.asyncio
class TestCheckDuplicateMatch:
    async def test_returns_app_data(self):
        app, job = _make_app_and_job()
        session = MagicMock()
        session.exec.return_value.first.return_value = (app, job)
        result = await check_duplicate_application(
            job_url="https://example.com/job/123",
            session=session,
            current_user=MagicMock(id=1),
        )
        assert result["is_duplicate"] is True
        existing = result["existing_application"]
        assert existing["id"] == 1
        assert existing["job_title"] == "Engineer"
        assert existing["company"] == "Acme"
        assert existing["status"] == "applied"
        assert existing["notes"] is None
        assert existing["cover_letter_body"] == "Dear..."

    async def test_cover_letter_none_body(self):
        app, job = _make_app_and_job(cover_body=None)
        app.cover_letter_final = {}
        session = MagicMock()
        session.exec.return_value.first.return_value = (app, job)
        result = await check_duplicate_application(
            job_url="https://example.com/job/123",
            session=session,
            current_user=MagicMock(id=1),
        )
        assert result["is_duplicate"] is True
        assert result["existing_application"]["cover_letter_body"] is None


@pytest.mark.asyncio
class TestUrlNormalization:
    async def test_www_normalized(self):
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        await check_duplicate_application(
            job_url="https://www.example.com/job/123",
            session=session,
            current_user=MagicMock(id=1),
        )
        call_args = session.exec.call_args[0][0]
        assert isinstance(call_args, Select)

    async def test_trailing_slash_normalized(self):
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        await check_duplicate_application(
            job_url="https://example.com/job/123/",
            session=session,
            current_user=MagicMock(id=1),
        )
        assert session.exec.called


@pytest.mark.asyncio
class TestLinkedInIdExtraction:
    async def test_collections_url_extracts_id(self):
        app, job = _make_app_and_job()
        job.url = "https://www.linkedin.com/jobs/view/4386770393/"
        session = MagicMock()
        session.exec.return_value.first.return_value = (app, job)
        result = await check_duplicate_application(
            job_url="https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4386770393",
            session=session,
            current_user=MagicMock(id=1),
        )
        assert result["is_duplicate"] is True

    async def test_view_url_extracts_id(self):
        app, job = _make_app_and_job()
        job.url = "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4386770393"
        session = MagicMock()
        session.exec.return_value.first.return_value = (app, job)
        result = await check_duplicate_application(
            job_url="https://www.linkedin.com/jobs/view/4386770393/",
            session=session,
            current_user=MagicMock(id=1),
        )
        assert result["is_duplicate"] is True

    async def test_non_linkedin_url_no_id_extraction(self):
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        await check_duplicate_application(
            job_url="https://indeed.com/viewjob?jk=abc123",
            session=session,
            current_user=MagicMock(id=1),
        )
        assert session.exec.called


@pytest.mark.asyncio
class TestErrorHandling:
    async def test_server_error_wraps_exception(self):
        session = MagicMock()
        session.exec.side_effect = RuntimeError("DB down")
        with pytest.raises(HTTPException) as exc:
            await check_duplicate_application(
                job_url="https://example.com/job/123",
                session=session,
                current_user=MagicMock(id=1),
            )
        assert exc.value.status_code == 500
        assert "Failed to check duplicate application" in exc.value.detail


@pytest.mark.asyncio
class TestStatusEnumSerialization:
    async def test_all_statuses_serialized(self):
        for status in ApplicationStatus:
            app, job = _make_app_and_job(status=status)
            session = MagicMock()
            session.exec.return_value.first.return_value = (app, job)
            result = await check_duplicate_application(
                job_url="https://example.com/job/123",
                session=session,
                current_user=MagicMock(id=1),
            )
            assert result["existing_application"]["status"] == status.value
