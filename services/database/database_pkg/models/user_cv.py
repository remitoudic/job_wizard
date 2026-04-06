from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class UserCVBase(SQLModel):
    name: str
    original_filename: str
    cv_url: str
    cv_data: Optional[str] = None
    is_active: bool = False


class UserCV(UserCVBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCVRead(UserCVBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class UserCVUpdate(SQLModel):
    name: Optional[str] = None
