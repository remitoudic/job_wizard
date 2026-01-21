"""Application model for storing complete job applications."""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from sqlmodel import Field, SQLModel, JSON, Column


class ApplicationStatus(str, Enum):
    """Enum for application status values."""
    APPLIED = "applied"
    WAITING = "waiting"
    INTERVIEW = "interview"
    FINISH = "finish"
    REFUSED = "refused"
    ACCEPTED = "accepted"


class Application(SQLModel, table=True):
    """Model for complete job application from Step 3 of the application workflow."""
    
    __tablename__ = "applications"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, description="User who created the application")
    job_description_id: int = Field(foreign_key="job_descriptions.id", index=True, description="Reference to the job description")
    generated_letter_id: Optional[int] = Field(default=None, foreign_key="generated_letters.id", index=True, description="Reference to generated letters")
    header: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON),
        description="Header information (name, contact details, etc.)"
    )
    cover_letter_final: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON),
        description="Final cover letter with structure: {model: str, timestamp: str, body: str}"
    )
    status: ApplicationStatus = Field(
        default=ApplicationStatus.APPLIED,
        description="Current status of the application"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when last updated")
