import secrets
import hashlib
from typing import List
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from database_pkg.models.api_key import (
    ApiKey,
    ApiKeyCreate,
    ApiKeyRead,
    ApiKeyWithSecret,
)

router = APIRouter(tags=["api-keys"])


def generate_key_and_hash():
    # Generate a random 32-byte URL-safe string
    raw_key = secrets.token_urlsafe(32)
    # The token given to the user looks like: jw_live_RANDOMSTRING
    token = f"jw_live_{raw_key}"
    # Hash the token using SHA-256
    key_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return token, key_hash


@router.post("", response_model=ApiKeyWithSecret)
async def create_api_key(
    request: ApiKeyCreate, session: SessionDep, current_user: CurrentUser
):
    assert current_user.id is not None

    # Generate token and hash
    token, key_hash = generate_key_and_hash()

    # Create DB record
    db_api_key = ApiKey(name=request.name, user_id=current_user.id, key_hash=key_hash)

    session.add(db_api_key)
    session.commit()
    session.refresh(db_api_key)

    # Return the secret token ONLY this once
    return ApiKeyWithSecret(
        id=db_api_key.id,  # type: ignore
        name=db_api_key.name,
        user_id=db_api_key.user_id,
        created_at=db_api_key.created_at,
        last_used_at=db_api_key.last_used_at,
        secret_key=token,
    )


@router.get("", response_model=List[ApiKeyRead])
async def list_api_keys(session: SessionDep, current_user: CurrentUser):
    assert current_user.id is not None
    statement = select(ApiKey).where(ApiKey.user_id == current_user.id)
    keys = session.exec(statement).all()
    return keys


@router.delete("/{key_id}")
async def delete_api_key(key_id: int, session: SessionDep, current_user: CurrentUser):
    assert current_user.id is not None
    statement = select(ApiKey).where(
        ApiKey.id == key_id, ApiKey.user_id == current_user.id
    )
    key = session.exec(statement).first()

    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")

    session.delete(key)
    session.commit()
    return {"success": True, "message": "API Key revoked successfully"}
