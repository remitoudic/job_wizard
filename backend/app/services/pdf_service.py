from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.colors import HexColor
from PIL import Image as PILImage
from typing import Optional
import os
import logfire


class PDFService:
    """Service for generating PDF cover letters"""
    
    def __init__(self):
        self.page_width, self.page_height = letter
        self.margin = 0.75 * inch
    
    def generate_cover_letter_pdf(
        self,
        output_path: str,
        cover_letter: str,
        job_title: str,
        company: str,
        template_name: str = "generic",
        user_name: str = "Applicant",
        image_path: Optional[str] = None,
        email: Optional[str] = "",
        phone: Optional[str] = "",
        linkedin: Optional[str] = "",
    ):
        """
        Generate a professional cover letter PDF using the specified template.
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )
        
        # Get template strategy
        from app.services.templates import TemplateRegistry
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
            image_path=image_path,
            email=email,
            phone=phone,
            linkedin=linkedin
        )
        
        # Build PDF
        try:
            logfire.info("Generating PDF", template=template_name, output=output_path)
            doc.build(story)
        except Exception as e:
            logfire.error("PDF generation failed", error=str(e))
            raise e
