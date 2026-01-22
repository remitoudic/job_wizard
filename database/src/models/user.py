from sqlmodel import SQLModel, Field
from typing import Optional

from datetime import datetime

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_superuser: bool = False

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    last_login: Optional[datetime] = None

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    last_login: Optional[datetime] = None

class UserUpdate(SQLModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
