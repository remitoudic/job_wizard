from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel, HttpUrl
from typing import Optional
import os
from pathlib import Path
import uuid
from datetime import datetime

from app.services.job_parser import JobParser
from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService

router = APIRouter()

# Initialize services
job_parser = JobParser()
llm_service = LLMService()
pdf_service = PDFService()

UPLOAD_DIR = Path("/app/uploads")


class JobURLRequest(BaseModel):
    url: HttpUrl
    # Optional raw Cookie header string to use for authenticated fetches (Playwright)
    cookie: Optional[str] = None


class JobDescription(BaseModel):
    title: str
    company: str
    description: str
    requirements: list[str]
    url: str


class CoverLetterRequest(BaseModel):
    job_description: JobDescription
    user_name: Optional[str] = "Applicant"
    user_skills: Optional[str] = ""


class CoverLetterResponse(BaseModel):
    cover_letter: str
    job_title: str
    company: str


@router.post("/parse-job", response_model=JobDescription)
async def parse_job_description(request: JobURLRequest):
    """
    Parse job description from a URL
    """
    try:
        job_data = await job_parser.parse_url(str(request.url), cookies=request.cookie)
        return job_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse job URL: {str(e)}")


@router.post("/generate-cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(request: CoverLetterRequest):
    """
    Generate a personalized cover letter using LLM
    """
    try:
        cover_letter = await llm_service.generate_cover_letter(
            job_description=request.job_description.description,
            job_title=request.job_description.title,
            company=request.job_description.company,
            requirements=request.job_description.requirements,
            user_name=request.user_name,
            user_skills=request.user_skills,
        )
        
        return CoverLetterResponse(
            cover_letter=cover_letter,
            job_title=request.job_description.title,
            company=request.job_description.company,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload user photo for cover letter
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix if file.filename else ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return {
            "filename": unique_filename,
            "url": f"/uploads/{unique_filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


@router.post("/generate-pdf")
async def generate_pdf(
    cover_letter: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    user_name: str = Form("Applicant"),
    image_filename: Optional[str] = Form(None),
):
    """
    Generate PDF with cover letter and optional user photo
    """
    try:
        # Get image path if provided
        image_path = None
        if image_filename:
            image_path = UPLOAD_DIR / image_filename
            if not image_path.exists():
                raise HTTPException(status_code=404, detail="Image not found")
        
        # Generate PDF
        pdf_filename = f"cover_letter_{uuid.uuid4()}.pdf"
        pdf_path = UPLOAD_DIR / pdf_filename
        
        pdf_service.generate_cover_letter_pdf(
            output_path=str(pdf_path),
            cover_letter=cover_letter,
            job_title=job_title,
            company=company,
            user_name=user_name,
            image_path=str(image_path) if image_path else None,
        )
        
        return {
            "filename": pdf_filename,
            "url": f"/uploads/{pdf_filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
