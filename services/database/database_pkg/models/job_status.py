"""JobStatus model for tracking background task progress."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, JSON, Column


class JobStatus(SQLModel, table=True):
    """Model for tracking status of async jobs (cover letter generation, parsing, etc.)."""
    
    __tablename__ = "job_status"
    
    # job_id is usually a UUID string from the frontend/API
    job_id: str = Field(primary_key=True, index=True, description="Unique identifier for the job")
    status: str = Field(description="Current status (extracting, generating, completed, error)")
    payload: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON),
        description="Data payload (result data or error message)"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, 
        description="Timestamp of last status update"
    )
