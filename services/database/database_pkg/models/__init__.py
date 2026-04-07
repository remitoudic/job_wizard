"""Models module for database tables."""
from .user import User
from .job_description import JobDescription
from .generated_letter import GeneratedLetter
from .application import Application, ApplicationStatus
from .job_status import JobStatus

__all__ = [
    "User",
    "JobDescription",
    "GeneratedLetter",
    "Application",
    "ApplicationStatus",
    "JobStatus",
]
