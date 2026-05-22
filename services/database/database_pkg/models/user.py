from sqlmodel import SQLModel, Field
from typing import Optional

from datetime import datetime


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    username: Optional[str] = Field(default=None, unique=True, index=True)
    first_name: Optional[str] = None
    surname: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None
    profile_picture_url: Optional[str] = None

    # Address fields
    street: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None

    phone: Optional[str] = None
    preferred_language: Optional[str] = Field(default="en")
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
    username: Optional[str] = None
    first_name: Optional[str] = None
    surname: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None
    profile_picture_url: Optional[str] = None

    street: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None

    phone: Optional[str] = None
    preferred_language: Optional[str] = None
    password: Optional[str] = None
