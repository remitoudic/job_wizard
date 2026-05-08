from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from .application import ApplicationStatus

class ApplicationStatusHistory(SQLModel, table=True):
    """Model for tracking history of application status changes."""
    
    __tablename__ = "application_status_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    application_id: int = Field(foreign_key="applications.id", index=True, description="The application being tracked")
    old_status: Optional[ApplicationStatus] = Field(default=None, description="The previous status")
    new_status: ApplicationStatus = Field(description="The new status set")
    notes: Optional[str] = Field(default=None, description="Optional note about this status change")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the change occurred")
