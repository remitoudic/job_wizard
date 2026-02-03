from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path
import uuid

from app.services.llm_service import LLMService
from app.services.pdf_service import PDFService
from app.services.pdf_parser import PDFParser
from app.services.backup_service import BackupService

# Import validation schemas
from app.api.validation.schemas import (
    CoverLetterRequest,
    CoverLetterResponse,
)

router = APIRouter(tags=["cover_letter"])

# Initialize services
llm_service = LLMService()
pdf_service = PDFService()
pdf_parser = PDFParser()
backup_service = BackupService()

UPLOAD_DIR = Path("/app/uploads")


@router.post("/generate-cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(request: CoverLetterRequest):
    """
    Generate a personalized cover letter using LLM
    """
    import asyncio
    
    try:
        # Create tasks for parallel execution
        generation_task = llm_service.generate_cover_letter(
            job_description=request.job_description.description,
            job_title=request.job_description.title,
            company=request.job_description.company,
            requirements=request.job_description.requirements,
            user_name=request.user_name,
            user_skills=request.user_skills,
            context_text=request.context_text,
            custom_instructions=request.custom_instructions,
        )

        extraction_task = None
        if request.context_text:
            extraction_task = asyncio.wait_for(
                llm_service.extract_contact_info(request.context_text), 
                timeout=20.0
            )

        # Execute tasks
        if extraction_task:
            results = await asyncio.gather(generation_task, extraction_task, return_exceptions=True)
            gen_result = results[0]
            extract_result = results[1]
        else:
            gen_result = await generation_task
            extract_result = {}

        # Handle Generation Result
        if isinstance(gen_result, Exception):
            raise gen_result
        
        cover_letter, source, alternative_id = gen_result

        # Handle Extraction Result
        contact_info = {"email": "", "phone": "", "linkedin": "", "name": "", "first_name": "", "surname": "", "address": "", "website": ""}
        if isinstance(extract_result, dict):
            contact_info = extract_result
        elif isinstance(extract_result, Exception):
             # Fail silently on extraction error, just log it if we had a logger
             pass

        return CoverLetterResponse(
            cover_letter=cover_letter,
            job_title=request.job_description.title,
            company=request.job_description.company,
            first_name=contact_info.get("first_name", ""),
            surname=contact_info.get("surname", ""),
            email=contact_info.get("email", ""),
            phone=contact_info.get("phone", ""),
            linkedin=contact_info.get("linkedin", ""),
            website=contact_info.get("website", ""),
            address=contact_info.get("address", ""),
            address_street=contact_info.get("address_street", ""),
            address_postcode=contact_info.get("address_postcode", ""),
            address_city=contact_info.get("address_city", ""),
            address_country=contact_info.get("address_country", ""),
            user_name_detected=contact_info.get("name", ""),
            source=source,
            alternative_id=alternative_id,
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


@router.get("/cover-letter/alternative/{alt_id}")
async def get_alternative_cover_letter(alt_id: str):
    """
    Get the alternative cover letter generated in the background
    """
    result = llm_service.get_alternative(alt_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alternative not found (or not ready yet)")
    return result


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


from app.api.deps import get_current_user_optional
from src.models.user import User

@router.post("/generate-pdf")
async def generate_pdf(
    current_user: Optional[User] = Depends(get_current_user_optional),
    cover_letter: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    user_name: Optional[str] = Form(""),
    first_name: Optional[str] = Form(""),
    surname: Optional[str] = Form(""),
    image_filename: Optional[str] = Form(None),
    email: Optional[str] = Form(""),
    phone: Optional[str] = Form(""),
    linkedin: Optional[str] = Form(""),
    template_name: str = Form("british"),
    custom_date: Optional[str] = Form(None),
    custom_subject: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),
    address: Optional[str] = Form(""),
    address_street: Optional[str] = Form(""),
    address_postcode: Optional[str] = Form(""),
    address_city: Optional[str] = Form(""),
    address_country: Optional[str] = Form(""),
):
    """
    Generate PDF with cover letter and optional user photo
    """
    try:
        # Generate filename
        pdf_filename = f"{uuid.uuid4()}.pdf"
        pdf_path = UPLOAD_DIR / pdf_filename

        # Resolve image path if provided
        image_path = None
        if image_filename:
            img_p = UPLOAD_DIR / image_filename
            if img_p.exists():
                image_path = str(img_p)

        # Generate PDF
        pdf_service.generate_cover_letter_pdf(
            output_path=str(pdf_path),
            cover_letter=cover_letter,
            job_title=job_title,
            company=company,
            template_name=template_name,
            user_name=user_name,
            first_name=first_name,
            surname=surname,
            image_path=image_path,
            email=email,
            phone=phone,
            linkedin=linkedin,
            custom_date=custom_date,
            custom_subject=custom_subject,
            full_name=full_name,
            address=address,
            address_street=address_street,
            address_postcode=address_postcode,
            address_city=address_city,
            address_country=address_country,
        )

        # Perform Backup
        # We try to use the most relevant date for the filename
        # Prioritize system date for consistent chronological sorting, or date of creation.
        # Requirement: "name of the cover letter should have the the user_id, date and company_applied"
        
        user_id_str = str(current_user.id) if current_user else "guest"
        
        backup_service.backup_cover_letter_pdf(
            source_path=str(pdf_path),
            user_id=user_id_str,
            company=company
        )

        
        return {
            "filename": pdf_filename,
            "url": f"/uploads/{pdf_filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a file from the uploads directory
    """
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )

