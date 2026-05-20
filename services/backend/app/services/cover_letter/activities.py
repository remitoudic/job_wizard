from temporalio import activity
from typing import Dict, Any
from app.services.cover_letter.llm_service import LLMService
from app.services.cover_letter.pdf_service import PDFService
from app.services.platform.backup_service import BackupService
from app.core.pubsub import pubsub_manager
import logging

logger = logging.getLogger(__name__)

# Module-level singletons — must be shared across activity calls
# in the same worker process so that semaphores, alternatives_store,
# and provider failover state are preserved.
_llm_service: LLMService | None = None
_pdf_service: PDFService | None = None
_backup_service: BackupService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_pdf_service() -> PDFService:
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service


def get_backup_service() -> BackupService:
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service


# Standalone activities (preferred for Temporal Python for simplicity/validation)


@activity.defn
async def extract_contact_info(text: str) -> Dict[str, Any]:
    """Activity to extract contact info from candidate text"""
    logger.info("Activity: Extracting contact info")
    return await get_llm_service().extract_contact_info(text)


@activity.defn
async def generate_text_race(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Activity to generate cover letter text using the race mode logic"""
    logger.info(
        f"Activity: Generating cover letter text for job {request_data.get('job_id')}"
    )

    # This will call the existing race mode logic
    text, source, alt_id = await get_llm_service().generate_cover_letter(
        job_description=request_data["job_description"]["description"],
        job_title=request_data["job_description"]["title"],
        company=request_data["job_description"]["company"],
        requirements=request_data["job_description"].get("requirements", []),
        job_id=request_data["job_id"],
        user_name=request_data.get("user_name", ""),
        user_skills=request_data.get("user_skills", ""),
        context_text=request_data.get("context_text"),
        custom_instructions=request_data.get("custom_instructions"),
        language=request_data.get("language", "english"),
    )

    return {"text": text, "source": source, "alternative_id": alt_id}


@activity.defn
async def render_pdf(pdf_data: Dict[str, Any]) -> Dict[str, Any]:
    """Activity to render the final PDF"""
    import uuid
    from pathlib import Path

    UPLOAD_DIR = Path("/app/uploads")
    pdf_filename = f"{uuid.uuid4()}.pdf"
    pdf_path = UPLOAD_DIR / pdf_filename

    logger.info(f"Activity: Rendering PDF to {pdf_path}")

    get_pdf_service().generate_cover_letter_pdf(output_path=str(pdf_path), **pdf_data)

    return {
        "filename": pdf_filename,
        "url": f"/uploads/{pdf_filename}",
        "path": str(pdf_path),
    }


@activity.defn
async def backup_pdf(backup_data: Dict[str, Any]) -> None:
    """Activity to backup the generated PDF"""
    logger.info(f"Activity: Backing up PDF for company {backup_data.get('company')}")

    get_backup_service().backup_cover_letter_pdf(
        source_path=backup_data["source_path"],
        user_id=backup_data["user_id"],
        company=backup_data["company"],
    )


@activity.defn
async def notify_status(payload: Dict[str, Any]) -> None:
    """Activity to push status updates to the SSE stream"""
    logger.info(
        f"Activity: Notifying status for job {payload.get('job_id')}: {payload.get('status')}"
    )
    await pubsub_manager.notify(payload)
