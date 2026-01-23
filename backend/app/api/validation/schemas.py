from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any

class JobURLRequest(BaseModel):
    url: str
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
    first_name: Optional[str] = ""
    surname: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    linkedin: Optional[str] = ""
    website: Optional[str] = ""
    address: Optional[str] = ""
    address_street: Optional[str] = ""
    address_postcode: Optional[str] = ""
    address_city: Optional[str] = ""
    address_country: Optional[str] = ""
    user_name_detected: Optional[str] = ""
    source: Optional[str] = "local"
    alternative_id: Optional[str] = ""


class GeneratedLetterData(BaseModel):
    """Individual generated letter from race mode."""
    model: str
    letter: str
    timestamp: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None



class SaveApplicationRequest(BaseModel):
    """Request model for saving complete application workflow."""
    # Job Description data
    job_url: str
    job_title: str
    job_company: str
    job_description: str
    job_requirements: List[str]
    job_source: str = "LinkedIn"
    
    # Generated letters (all versions from race mode)
    generated_letters: List[GeneratedLetterData]
    
    # Final application data
    selected_letter_index: int = 0
    header: Dict[str, Any]  # Contains name, email, phone, address fields, etc.
    cover_letter_body: str  # Final edited cover letter text
    

class SaveApplicationResponse(BaseModel):
    """Response model after saving application."""
    success: bool
    application_id: int
    job_description_id: int
    generated_letter_id: int
    message: str = "Application saved successfully"
