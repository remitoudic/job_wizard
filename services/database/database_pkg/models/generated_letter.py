"""GeneratedLetter model for storing AI-generated cover letters."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import Field, SQLModel, JSON, Column


class GeneratedLetter(SQLModel, table=True):
    """Model for AI-generated cover letters from Step 2 of the application workflow."""

    __tablename__ = "generated_letters"

    id: Optional[int] = Field(default=None, primary_key=True)
    application_id: Optional[int] = Field(
        default=None,
        foreign_key="applications.id",
        index=True,
        description="Reference to the application",
    )
    user_id: int = Field(
        foreign_key="user.id", index=True, description="User who generated the letters"
    )
    generated_letters: List[Dict[str, Any]] = Field(
        default=[],
        sa_column=Column(JSON),
        description="Array of generated letters with structure: [{model: str, letter: str, timestamp: str}]",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when last updated"
    )
