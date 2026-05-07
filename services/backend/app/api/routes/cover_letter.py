from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path
import uuid

from app.services.cover_letter.llm_service import LLMService
from app.services.cover_letter.pdf_service import PDFService
from app.services.cover_letter.pdf_parser import PDFParser
from app.services.platform.backup_service import BackupService
from app.services.cover_letter.workflows import CoverLetterWorkflow

from app.api.validation.schemas import (
    CoverLetterRequest,
    CoverLetterResponse,
)
from app.core.pubsub import pubsub_manager
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
from app.core.temporal import get_temporal_client
from app.api.deps import get_current_user_optional, CurrentUser
from database_pkg.models.user import User

router = APIRouter(tags=["cover_letter"])

# Initialize services
llm_service = LLMService()
pdf_service = PDFService()
pdf_parser = PDFParser()
backup_service = BackupService()

UPLOAD_DIR = Path("/app/uploads")


@router.post("/generate-cover-letter")
async def generate_cover_letter(request: CoverLetterRequest):
    """
    Start the asynchronous generation of a cover letter.
    Returns a job_id that can be used to listen for events.
    """
    job_id = str(uuid.uuid4())
    
    # Start the Temporal Workflow
    try:
        temporal_client = await get_temporal_client()
        
        # Inject job_id into the request data for tracking inside the workflow/activities
        workflow_data = request.model_dump()
        workflow_data["job_id"] = job_id
        
        # --- Pre-processing for stored CVs to bypass bottleneck ---
        # If context_text is a JSON string of CVData (which activeCV passes),
        # we can instantly extract contact info and compress the payload.
        if workflow_data.get("context_text"):
            try:
                cv_dict = json.loads(workflow_data["context_text"])
                if isinstance(cv_dict, dict) and "contact" in cv_dict:
                    # 1. Skip LLM extraction by pre-filling contact_info
                    workflow_data["contact_info"] = cv_dict.get("contact", {})
                    
                    # 2. Compact JSON to Markdown prose to save tokens & improve generation quality
                    prose = []
                    if cv_dict.get("summary"):
                        prose.append(f"Summary: {cv_dict['summary']}\n")
                    
                    if cv_dict.get("experiences"):
                        prose.append("Experience:")
                        for exp in cv_dict["experiences"]:
                            desc = exp.get("description", "").strip()
                            prose.append(f"- {exp.get('title', 'Role')} at {exp.get('company', 'Company')} ({exp.get('start_date', '')} to {exp.get('end_date', '')})")
                            if desc:
                                prose.append(f"  {desc}")
                        prose.append("")
                        
                    if cv_dict.get("education"):
                        prose.append("Education:")
                        for edu in cv_dict["education"]:
                            prose.append(f"- {edu.get('degree', '')} in {edu.get('field_of_study', '')} from {edu.get('institution', '')}")
                        prose.append("")
                        
                    if cv_dict.get("skills"):
                        prose.append(f"Skills: {', '.join(cv_dict['skills'])}")
                        
                    workflow_data["context_text"] = "\n".join(prose)
            except Exception:
                pass # Not JSON, treat as raw text for normal extraction
        
        await temporal_client.start_workflow(
            CoverLetterWorkflow.run,
            workflow_data,
            id=job_id,
            task_queue="cover-letter-tasks",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")
    
    return {"job_id": job_id}


@router.get("/events/{job_id}")
async def cover_letter_events(job_id: str):
    """
    SSE endpoint to listen for cover letter generation events for a specific job_id.
    Includes initial synchronization to replay the latest status if it exists.
    """
    async def event_generator():
        try:
            # 1. Initial Sync (Replay latest status if it exists)
            last_status = await pubsub_manager.get_job_status(job_id)
            if last_status:
                yield {
                    "event": "message",
                    "id": str(uuid.uuid4()),
                    "data": json.dumps(last_status["payload"])
                }
                
                # If the job was already terminal, stop here
                if last_status["status"] in ("completed", "error"):
                    return

            # 2. Regular Subscription
            async for msg in pubsub_manager.subscribe():
                # Filter by job_id
                if msg.get("job_id") == job_id:
                    yield {
                        "event": "message",
                        "id": str(uuid.uuid4()),
                        "data": json.dumps(msg)
                    }
                    
                    # Terminate stream on completion or error
                    if msg.get("status") in ("completed", "error"):
                        break
        except asyncio.CancelledError:
            # Handle client disconnect
            pass
            
    return EventSourceResponse(event_generator())


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
            "url": f"/api/uploads/{unique_filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


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
            "url": f"/api/download/{pdf_filename}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str, current_user: CurrentUser):
    """
    Download a file from the uploads directory.
    Requires authentication.
    """
    # Sanitize filename by taking only the basename
    safe_filename = Path(filename).name
    file_path = UPLOAD_DIR / safe_filename
    
    # Ensure the file exists and is a file
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Extra security: Ensure the resolved path is within the UPLOAD_DIR
    try:
        # resolve() handles symlinks and '..'
        resolved_path = file_path.resolve()
        if not str(resolved_path).startswith(str(UPLOAD_DIR.resolve())):
             raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type='application/pdf'
    )


@router.get("/uploads/{filename}")
async def get_upload(filename: str, current_user: CurrentUser):
    """
    Authenticated endpoint to serve uploaded files (images, etc).
    Replaces the previous unauthenticated static mount.
    """
    safe_filename = Path(filename).name
    file_path = UPLOAD_DIR / safe_filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        resolved_path = file_path.resolve()
        if not str(resolved_path).startswith(str(UPLOAD_DIR.resolve())):
             raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")

    # Determine media type based on extension
    ext = Path(safe_filename).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".pdf": "application/pdf",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(path=file_path, media_type=media_type)

