from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session
from app.core.db import get_session
from app.core.security import SECRET_KEY, ALGORITHM
from app.api.validation.schemas import TokenData
from database_pkg.models.user import User
from app.services.platform.user import user_service

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
reusable_oauth2_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]

def get_current_user(
    session: SessionDep, 
    request: Request,
    token: Annotated[str | None, Depends(reusable_oauth2_optional)] = None
) -> User:
    # 1. Try to get token from Authorization header (via reusable_oauth2_optional)
    # 2. If not found, try to get from cookie
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = user_service.get_by_email(session, email=token_data.username) # Using email as sub
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_user_optional(
    session: SessionDep, 
    request: Request,
    token: Annotated[str | None, Depends(reusable_oauth2_optional)] = None
) -> User | None:
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except JWTError:
        return None
    
    user = user_service.get_by_email(session, email=token_data.username)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
