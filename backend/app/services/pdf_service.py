from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.colors import HexColor
from PIL import Image as PILImage
from typing import Optional
import os


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
        user_name: str = "Applicant",
        image_path: Optional[str] = None,
        email: Optional[str] = "",
        phone: Optional[str] = "",
        linkedin: Optional[str] = "",
    ):
        """
        Generate a professional cover letter PDF
        
        Args:
            output_path: Path to save the PDF
            cover_letter: Cover letter text
            job_title: Job title
            company: Company name
            user_name: Applicant's name
            image_path: Optional path to user's photo
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
        
        # Container for PDF elements
        story = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=6,
            alignment=TA_CENTER,
        )
        
        contact_style = ParagraphStyle(
            'CustomContact',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#1a1a1a'),
            leading=16,
            alignment=TA_LEFT,
            spaceAfter=12,
        )
        
        # Add user photo if provided
        if image_path and os.path.exists(image_path):
            try:
                # Open and resize image
                img = PILImage.open(image_path)
                
                # Calculate dimensions (max 1.5 inches)
                max_size = 1.5 * inch
                img_width, img_height = img.size
                aspect = img_height / img_width
                
                if aspect > 1:  # Portrait
                    height = max_size
                    width = max_size / aspect
                else:  # Landscape or square
                    width = max_size
                    height = max_size * aspect
                
                # Create ReportLab image
                photo = Image(image_path, width=width, height=height)
                
                # Center the image
                photo.hAlign = 'CENTER'
                story.append(photo)
                story.append(Spacer(1, 0.3 * inch))
                
            except Exception as e:
                print(f"Warning: Could not add image to PDF: {e}")
        
        # Add applicant name
        story.append(Paragraph(user_name, title_style))
        story.append(Spacer(1, 0.05 * inch))
        
        # Add contact info if present
        contact_parts = []
        if email:
            contact_parts.append(email)
        if phone:
            contact_parts.append(phone)
        if linkedin:
            contact_parts.append(linkedin)
            
        if contact_parts:
            contact_text = " | ".join(contact_parts)
            story.append(Paragraph(contact_text, contact_style))
        else:
            story.append(Spacer(1, 0.1 * inch))
        
        # Add job title and company
        subtitle_text = f"Application for {job_title} at {company}"
        story.append(Paragraph(subtitle_text, subtitle_style))
        
        # Add cover letter content
        # Split into paragraphs
        paragraphs = cover_letter.split('\n\n')
        
        for para in paragraphs:
            if para.strip():
                # Clean up the text
                para_text = para.strip().replace('\n', ' ')
                story.append(Paragraph(para_text, body_style))
                story.append(Spacer(1, 0.15 * inch))
        
        # Build PDF
        doc.build(story)
