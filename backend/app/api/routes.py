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
from app.services.pdf_parser import PDFParser

router = APIRouter()

# Initialize services
job_parser = JobParser()
llm_service = LLMService()
pdf_service = PDFService()
pdf_parser = PDFParser()

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
    source: Optional[str] = None


class CoverLetterRequest(BaseModel):
    job_description: JobDescription
    user_name: Optional[str] = "Applicant"
    user_skills: Optional[str] = ""
    context_text: Optional[str] = None


class CoverLetterResponse(BaseModel):
    cover_letter: str
    job_title: str
    company: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    linkedin: Optional[str] = ""


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
            context_text=request.context_text,
        )
        
        # Extract contact info if context provided
        contact_info = {"email": "", "phone": "", "linkedin": ""}
        if request.context_text:
            try:
                contact_info = await llm_service.extract_contact_info(request.context_text)
            except Exception:
                pass # Fail silently on extraction

        return CoverLetterResponse(
            cover_letter=cover_letter,
            job_title=request.job_description.title,
            company=request.job_description.company,
            email=contact_info.get("email", ""),
            phone=contact_info.get("phone", ""),
            linkedin=contact_info.get("linkedin", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")


@router.post("/upload-context")
async def upload_context(file: UploadFile = File(...)):
    """
    Upload context file (PDF) for cover letter personalization
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.pdf"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Parse text
        text = pdf_parser.extract_text(file_path)
        
        # Clean up file (optional, but good for privacy/space if we only need text)
        # For now, let's keep it in case we need to refer back or debug
        # os.remove(file_path)
        
        return {
            "filename": unique_filename,
            "text": text,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process context file: {str(e)}")


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
    email: Optional[str] = Form(""),
    phone: Optional[str] = Form(""),
    linkedin: Optional[str] = Form(""),
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
            email=email,
            phone=phone,
            linkedin=linkedin,
        )
        
        return {
            "filename": pdf_filename,
            "url": f"/uploads/{pdf_filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
