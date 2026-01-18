from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import select
from app.api.deps import SessionDep, CurrentUser, get_current_superuser
from src.models.user import UserRead, UserUpdate, User
from app.services.user import user_service

router = APIRouter()

@router.get("/", response_model=List[UserRead])
def read_users(
    session: SessionDep,
    current_user: User = Depends(get_current_superuser),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve users.
    """
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()
    return users

@router.get("/me", response_model=UserRead)
def read_user_me(current_user: CurrentUser):
    return current_user

@router.patch("/me", response_model=UserRead)
def update_user_me(
    session: SessionDep, 
    current_user: CurrentUser, 
    user_in: UserUpdate
):
    current_user = user_service.update(session, db_user=current_user, user_in=user_in)
    return current_user
