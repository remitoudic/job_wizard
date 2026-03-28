from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import SessionDep
from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.api.validation.schemas import Token
from database_pkg.models.user import UserCreate, User
from app.services.platform.user import user_service

router = APIRouter()

@router.post("/login", response_model=Token)
def login_for_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = user_service.authenticate(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    
    # Update last login
    user_service.update_last_login(session, user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/register", response_model=User) # Should probably return UserRead but User is fine for now
def register_user(session: SessionDep, user_in: UserCreate) -> User:
    user = user_service.get_by_email(session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists",
        )
    user = user_service.create(session, user_in)
    return user
