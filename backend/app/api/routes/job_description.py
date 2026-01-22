from fastapi import APIRouter, HTTPException
from app.services.job_parser import JobParser

# Import validation schemas
from app.api.validation.schemas import (
    JobURLRequest,
    JobDescription,
)

# Import database models
from src.models import JobDescription as DBJobDescription

router = APIRouter(tags=["job_description"])

# Initialize services
job_parser = JobParser()


@router.post("/parse-job", response_model=JobDescription)
async def parse_job_description(request: JobURLRequest):
    """
    Parse job description from a URL
    """
    import logfire
    
    try:
        logfire.info("Job parsing requested", url=str(request.url))
        job_data = await job_parser.parse_url(str(request.url), cookies=request.cookie)
        logfire.info("Job parsing successful", url=str(request.url), title=job_data.get("title"))
        return job_data
    except Exception as e:
        error_msg = str(e)
        logfire.error("Job parsing failed", url=str(request.url), error=error_msg, error_type=type(e).__name__)
        
        # Categorize errors for better user feedback
        if "timeout" in error_msg.lower():
            user_message = "The job page took too long to load. Please try again or check if the URL is accessible."
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            user_message = "Access to this job posting is restricted. The site may require login or have blocked automated access."
        elif "404" in error_msg or "not found" in error_msg.lower():
            user_message = "Job posting not found. The URL may be incorrect or the posting may have been removed."
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            user_message = "Too many requests. Please wait a moment and try again."
        elif "dns" in error_msg.lower() or "resolve" in error_msg.lower():
            user_message = "Could not reach the website. Please check the URL and your internet connection."
        elif "playwright" in error_msg.lower():
            user_message = f"Browser automation failed: {error_msg}"
        elif "parse" in error_msg.lower() or "extract" in error_msg.lower():
            user_message = "Could not extract job details from this page. The page structure may not be supported."
        else:
            user_message = f"Failed to parse job URL: {error_msg}"
        
        raise HTTPException(status_code=400, detail=user_message)

# End of General Routes
