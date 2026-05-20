"""
User CV management routes — upload, list, rename, activate, delete.
"""

import uuid
import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep, CurrentUser
from database_pkg.models.user_cv import UserCV, UserCVRead, UserCVUpdate
from app.services.platform.cloudinary_service import cloudinary_service
from app.services.cv_refresh.cv_parsers.cv_parser_service import cv_parser_service

logger = logging.getLogger("app.api.routes.user_cv")

router = APIRouter(tags=["user_cv"])

UPLOAD_DIR = Path("/app/uploads")
MAX_CVS_PER_USER = 5
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.get("/", response_model=list[UserCVRead])
def list_user_cvs(session: SessionDep, current_user: CurrentUser):
    """List all CVs for the current user."""
    statement = (
        select(UserCV)
        .where(UserCV.user_id == current_user.id)
        .order_by(UserCV.is_active.desc(), UserCV.created_at.desc())
    )
    return session.exec(statement).all()


@router.post("/", response_model=UserCVRead)
async def upload_user_cv(
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    name: str = Form("My CV"),
):
    """Upload a new CV (PDF). Max 5 per user, 10MB limit."""
    # Check CV count limit
    existing_count = len(
        session.exec(select(UserCV).where(UserCV.user_id == current_user.id)).all()
    )
    if existing_count >= MAX_CVS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_CVS_PER_USER} CVs allowed. Please delete one first.",
        )

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        # Upload raw PDF to Cloudinary
        file_id = str(uuid.uuid4())[:8]
        cv_url = cloudinary_service.upload_raw_file(content, current_user.id, file_id)

        # Save temporarily for parsing
        temp_path = UPLOAD_DIR / f"cv_temp_{file_id}.pdf"
        temp_path.write_bytes(content)

        # Parse CV
        cv_data_str = None
        try:
            cv_data = await cv_parser_service.parse_pdf(str(temp_path))
            cv_data_str = json.dumps(cv_data.model_dump())
        except Exception as e:
            logger.warning(f"CV parsing failed (file still saved): {e}")

        # Clean up temp file
        try:
            temp_path.unlink()
        except OSError:
            pass

        # Auto-activate if this is the first CV
        is_first = existing_count == 0

        db_cv = UserCV(
            user_id=current_user.id,
            name=name,
            original_filename=file.filename,
            cv_url=cv_url,
            cv_data=cv_data_str,
            is_active=is_first,
        )
        session.add(db_cv)
        session.commit()
        session.refresh(db_cv)

        return db_cv

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload CV: {str(e)}")


@router.patch("/{cv_id}", response_model=UserCVRead)
def update_user_cv(
    cv_id: int,
    cv_update: UserCVUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    """Update CV metadata (rename)."""
    db_cv = session.exec(
        select(UserCV).where(UserCV.id == cv_id, UserCV.user_id == current_user.id)
    ).first()
    if not db_cv:
        raise HTTPException(status_code=404, detail="CV not found")

    update_data = cv_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cv, key, value)
    db_cv.updated_at = datetime.utcnow()

    session.add(db_cv)
    session.commit()
    session.refresh(db_cv)
    return db_cv


@router.patch("/{cv_id}/activate", response_model=UserCVRead)
def activate_user_cv(
    cv_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    """Set a CV as the active one (deactivates all others)."""
    db_cv = session.exec(
        select(UserCV).where(UserCV.id == cv_id, UserCV.user_id == current_user.id)
    ).first()
    if not db_cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Deactivate all other CVs
    all_cvs = session.exec(
        select(UserCV).where(UserCV.user_id == current_user.id)
    ).all()
    for cv in all_cvs:
        cv.is_active = cv.id == cv_id
        cv.updated_at = datetime.utcnow()
        session.add(cv)

    session.commit()
    session.refresh(db_cv)
    return db_cv


@router.delete("/{cv_id}")
def delete_user_cv(
    cv_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    """Delete a CV (removes from Cloudinary and database)."""
    db_cv = session.exec(
        select(UserCV).where(UserCV.id == cv_id, UserCV.user_id == current_user.id)
    ).first()
    if not db_cv:
        raise HTTPException(status_code=404, detail="CV not found")

    # Delete from Cloudinary
    if db_cv.cv_url:
        cloudinary_service.delete_raw_file(db_cv.cv_url)

    was_active = db_cv.is_active
    session.delete(db_cv)
    session.commit()

    # If the deleted CV was active, activate the most recent remaining one
    if was_active:
        remaining = session.exec(
            select(UserCV)
            .where(UserCV.user_id == current_user.id)
            .order_by(UserCV.created_at.desc())
        ).first()
        if remaining:
            remaining.is_active = True
            remaining.updated_at = datetime.utcnow()
            session.add(remaining)
            session.commit()

    return {"detail": "CV deleted"}
