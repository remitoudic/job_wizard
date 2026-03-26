"""
CV Refresh API routes — upload, parse, list templates, generate PDF.
"""
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.cv_refresh.cv_parsers.cv_parser_service import (
    CVData,
    cv_parser_service,
)
from app.services.cv_refresh.cv_generator_service import cv_generator_service

logger = logging.getLogger("app.api.routes.cv_refresh")

router = APIRouter(tags=["cv_refresh"])

UPLOAD_DIR = Path("/app/uploads")


# ── Request / Response models ────────────────────────────────────────────────

class CVGenerateRequest(BaseModel):
    """Request body for CV generation."""
    cv_data: CVData
    template_name: str = "modern"


class CVTemplateResponse(BaseModel):
    name: str
    label: str
    description: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload a PDF CV, parse it with LlamaParse, and return structured CVData.
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        # Save to temp location
        unique_filename = f"cv_{uuid.uuid4()}.pdf"
        file_path = UPLOAD_DIR / unique_filename

        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        file_path.write_bytes(content)
        logger.info(f"Saved uploaded CV as {unique_filename} ({len(content)} bytes)")

        # Parse with LlamaParse
        cv_data = await cv_parser_service.parse_pdf(str(file_path))

        # Clean up the uploaded file (we only need the structured data now)
        try:
            file_path.unlink()
        except OSError:
            pass

        return cv_data.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV upload/parse failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse CV: {str(e)}",
        )


@router.get("/cv/templates", response_model=list[CVTemplateResponse])
async def list_cv_templates():
    """List all available CV templates."""
    templates = cv_generator_service.list_templates()
    return [t.to_dict() for t in templates]


@router.post("/cv/generate")
async def generate_cv(request: CVGenerateRequest):
    """
    Accept CVData + template name, generate and return a PDF file.
    """
    try:
        pdf_bytes = cv_generator_service.generate_pdf(
            cv_data=request.cv_data,
            template_name=request.template_name,
        )

        filename = f"cv_{uuid.uuid4()}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"CV generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate CV: {str(e)}",
        )
