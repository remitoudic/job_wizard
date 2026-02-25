from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
from typing import Optional
import logfire


class PDFService:
    """Service for generating PDF cover letters"""
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 0.75 * inch
    
    def generate_cover_letter_pdf(
        self,
        output_path: str,
        cover_letter: str,
        job_title: str,
        company: str,
        template_name: str = "british",
        user_name: str = "",
        first_name: str = "",
        surname: str = "",
        image_path: Optional[str] = None,
        email: Optional[str] = "",
        phone: Optional[str] = "",
        linkedin: Optional[str] = "",
        custom_date: Optional[str] = None,
        custom_subject: Optional[str] = None,
        full_name: Optional[str] = None,
        address: Optional[str] = "",
        address_street: Optional[str] = "",
        address_postcode: Optional[str] = "",
        address_city: Optional[str] = "",
        address_country: Optional[str] = "",
        employer_address: Optional[str] = "",
        recipient_name: Optional[str] = "",
    ):
        """
        Generate a professional cover letter PDF using the specified template.
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )
        
        # Get template strategy
        from app.services.cover_letter.templates import TemplateRegistry
        template = TemplateRegistry.get(template_name)
        
        # Prepare story container
        story = []
        
        # Delegate generation to strategy
        template.generate(
            doc=doc,
            story=story,
            cover_letter=cover_letter,
            job_title=job_title,
            company=company,
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
            employer_address=employer_address,
            recipient_name=recipient_name,
        )
        
        # Build PDF
        try:
            logfire.info("Generating PDF", template=template_name, output=output_path)
            doc.build(story)
        except Exception as e:
            logfire.error("PDF generation failed", error=str(e))
            raise e
