"""JobDescription model for storing parsed job postings."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import Text


class JobDescription(SQLModel, table=True):
    """Model for job descriptions parsed in Step 1 of the application workflow."""
    
    __tablename__ = "job_descriptions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(max_length=2048, index=True, description="URL of the job posting")
    full_description: str = Field(sa_column=Column(Text), description="Full job description text")
    requirements: List[str] = Field(default=[], sa_column=Column(JSON), description="Parsed job requirements as JSON array")
    job_title: Optional[str] = Field(default=None, max_length=512, description="Job title")
    company: Optional[str] = Field(default=None, max_length=512, description="Company name")
    source: str = Field(max_length=128, description="Source of the job (e.g., 'LinkedIn', 'Indeed')")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when parsed")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when last updated")
