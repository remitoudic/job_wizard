"""Unit tests for database models."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from database_pkg.models import (
    Application,
    ApplicationStatus,
    GeneratedLetter,
    JobDescription,
    User,
)


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="fake_hash",
        first_name="Test",
        surname="User",
        username="testuser",
        is_superuser=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestJobDescription:
    """Tests for JobDescription model."""

    def test_create_job_description(self, session: Session):
        """Test creating a job description."""
        job_desc = JobDescription(
            url="https://example.com/job/123",
            full_description="Full job description text here",
            requirements=["Python", "FastAPI", "PostgreSQL"],
            job_title="Senior Backend Developer",
            company="TechCorp",
            source="LinkedIn",
        )
        session.add(job_desc)
        session.commit()
        session.refresh(job_desc)

        assert job_desc.id is not None
        assert job_desc.url == "https://example.com/job/123"
        assert job_desc.job_title == "Senior Backend Developer"
        assert job_desc.company == "TechCorp"
        assert len(job_desc.requirements) == 3
        assert "Python" in job_desc.requirements
        assert isinstance(job_desc.created_at, datetime)
        assert isinstance(job_desc.updated_at, datetime)

    def test_job_description_json_requirements(self, session: Session):
        """Test that requirements are stored and retrieved as JSON."""
        requirements = ["React", "TypeScript", "Node.js", "AWS"]
        job_desc = JobDescription(
            url="https://example.com/job/456",
            full_description="Frontend developer position",
            requirements=requirements,
            job_title="Frontend Developer",
            company="StartupCo",
            source="Indeed",
        )
        session.add(job_desc)
        session.commit()
        session.refresh(job_desc)

        # Verify JSON storage and retrieval
        assert job_desc.requirements == requirements
        assert isinstance(job_desc.requirements, list)


class TestGeneratedLetter:
    """Tests for GeneratedLetter model."""

    def test_create_generated_letter(self, session: Session, test_user: User):
        """Test creating a generated letter."""
        generated_letters_data = [
            {
                "model": "gpt-4",
                "letter": "Dear Hiring Manager...",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "model": "claude-3",
                "letter": "To whom it may concern...",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]

        gen_letter = GeneratedLetter(
            user_id=test_user.id,
            generated_letters=generated_letters_data,
        )
        session.add(gen_letter)
        session.commit()
        session.refresh(gen_letter)

        assert gen_letter.id is not None
        assert gen_letter.user_id == test_user.id
        assert len(gen_letter.generated_letters) == 2
        assert gen_letter.generated_letters[0]["model"] == "gpt-4"
        assert isinstance(gen_letter.created_at, datetime)

    def test_generated_letter_empty_list(self, session: Session, test_user: User):
        """Test creating a generated letter with empty list."""
        gen_letter = GeneratedLetter(
            user_id=test_user.id,
            generated_letters=[],
        )
        session.add(gen_letter)
        session.commit()
        session.refresh(gen_letter)

        assert gen_letter.generated_letters == []


class TestApplication:
    """Tests for Application model."""

    def test_create_application(self, session: Session, test_user: User):
        """Test creating a complete application."""
        # Create job description
        job_desc = JobDescription(
            url="https://example.com/job/789",
            full_description="Python developer needed",
            requirements=["Python", "Django"],
            job_title="Python Developer",
            company="DevCorp",
            source="LinkedIn",
        )
        session.add(job_desc)
        session.commit()
        session.refresh(job_desc)

        # Create generated letter
        gen_letter = GeneratedLetter(
            user_id=test_user.id,
            generated_letters=[
                {
                    "model": "gpt-4",
                    "letter": "Cover letter text",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
        )
        session.add(gen_letter)
        session.commit()
        session.refresh(gen_letter)

        # Create application
        header = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "address": "123 Main St, City, Country",
        }
        cover_letter_final = {
            "model": "gpt-4",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "body": "Final cover letter text",
        }

        application = Application(
            user_id=test_user.id,
            job_description_id=job_desc.id,
            generated_letter_id=gen_letter.id,
            header=header,
            cover_letter_final=cover_letter_final,
            status=ApplicationStatus.APPLIED,
        )
        session.add(application)
        session.commit()
        session.refresh(application)

        assert application.id is not None
        assert application.user_id == test_user.id
        assert application.job_description_id == job_desc.id
        assert application.generated_letter_id == gen_letter.id
        assert application.header["name"] == "John Doe"
        assert application.cover_letter_final["model"] == "gpt-4"
        assert application.status == ApplicationStatus.APPLIED
        assert isinstance(application.created_at, datetime)

    def test_application_status_enum(self, session: Session, test_user: User):
        """Test all application status values."""
        job_desc = JobDescription(
            url="https://example.com/job/999",
            full_description="Test job",
            requirements=[],
            source="Test",
        )
        session.add(job_desc)
        session.commit()
        session.refresh(job_desc)

        # Test all status values
        statuses = [
            ApplicationStatus.APPLIED,
            ApplicationStatus.WAITING,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.FINISH,
            ApplicationStatus.REFUSED,
            ApplicationStatus.ACCEPTED,
        ]

        for status in statuses:
            app = Application(
                user_id=test_user.id,
                job_description_id=job_desc.id,
                status=status,
            )
            session.add(app)
            session.commit()
            session.refresh(app)

            assert app.status == status
            assert isinstance(app.status, ApplicationStatus)

    def test_application_without_generated_letter(
        self, session: Session, test_user: User
    ):
        """Test creating application without a generated letter (optional FK)."""
        job_desc = JobDescription(
            url="https://example.com/job/111",
            full_description="Quick apply job",
            requirements=[],
            source="Test",
        )
        session.add(job_desc)
        session.commit()
        session.refresh(job_desc)

        application = Application(
            user_id=test_user.id,
            job_description_id=job_desc.id,
            status=ApplicationStatus.WAITING,
        )
        session.add(application)
        session.commit()
        session.refresh(application)

        assert application.id is not None
        assert application.generated_letter_id is None


class TestModelRelationships:
    """Tests for relationships between models."""

    def test_full_workflow(self, session: Session, test_user: User):
        """Test the complete workflow from job description to application."""
        # Step 1: Parse job description
        job_desc = JobDescription(
            url="https://example.com/job/workflow",
            full_description="Complete workflow test job",
            requirements=["Python", "PostgreSQL", "Docker"],
            job_title="Full Stack Developer",
            company="WorkflowCorp",
            source="LinkedIn",
        )
        session.add(job_desc)
        session.commit()
        session.refresh(job_desc)

        # Step 2: Generate cover letters
        gen_letter = GeneratedLetter(
            user_id=test_user.id,
            generated_letters=[
                {
                    "model": "gpt-4",
                    "letter": "First draft...",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "model": "claude-3",
                    "letter": "Second draft...",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            ],
        )
        session.add(gen_letter)
        session.commit()
        session.refresh(gen_letter)

        # Step 3: Create final application
        application = Application(
            user_id=test_user.id,
            job_description_id=job_desc.id,
            generated_letter_id=gen_letter.id,
            header={
                "name": "Test User",
                "email": "test@example.com",
            },
            cover_letter_final={
                "model": "gpt-4",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "body": "Final selected letter",
            },
            status=ApplicationStatus.APPLIED,
        )
        session.add(application)
        session.commit()
        session.refresh(application)

        # Verify all relationships
        assert application.user_id == test_user.id
        assert application.job_description_id == job_desc.id
        assert application.generated_letter_id == gen_letter.id

        # Verify we can query back
        retrieved_app = session.get(Application, application.id)
        assert retrieved_app is not None
        assert retrieved_app.status == ApplicationStatus.APPLIED
