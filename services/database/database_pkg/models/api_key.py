from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class ApiKeyBase(SQLModel):
    name: str = Field(index=True)
    user_id: int = Field(foreign_key="user.id", index=True)


class ApiKey(ApiKeyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key_hash: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyRead(ApiKeyBase):
    id: int
    created_at: datetime
    last_used_at: Optional[datetime] = None


class ApiKeyWithSecret(ApiKeyRead):
    secret_key: str
