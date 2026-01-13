from abc import ABC, abstractmethod
from typing import Optional, List
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from PIL import Image as PILImage
import os

class BaseTemplate(ABC):
    """Abstract base class for cover letter PDF templates."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Define custom paragraph styles."""
        # Clean defaults to avoid pollution
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=6,
            alignment=TA_CENTER,
        )
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
        )
        self.contact_style = ParagraphStyle(
            'CustomContact',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=HexColor('#666666'),
            spaceAfter=5,
        )
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=HexColor('#1a1a1a'),
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
        )

    def _add_user_photo(self, story: List, image_path: Optional[str]):
        """Helper to add user photo to the story."""
        if image_path and os.path.exists(image_path):
            try:
                img = PILImage.open(image_path)
                max_size = 1.5 * inch
                img_width, img_height = img.size
                aspect = img_height / img_width
                
                if aspect > 1:
                    height = max_size
                    width = max_size / aspect
                else:
                    width = max_size
                    height = max_size * aspect
                
                photo = Image(image_path, width=width, height=height)
                photo.hAlign = 'CENTER' # Default to center, templates can override
                story.append(photo)
                story.append(Spacer(1, 0.3 * inch))
            except Exception as e:
                print(f"Warning: Could not add image to PDF: {e}")

    def _add_paragraphs(self, story: List, text: str):
        """Helper to add cover letter body paragraphs."""
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                para_text = para.strip().replace('\n', ' ')
                story.append(Paragraph(para_text, self.body_style))
                story.append(Spacer(1, 0.15 * inch))

    @abstractmethod
    def generate(
        self,
        doc: SimpleDocTemplate,
        story: List,
        cover_letter: str,
        job_title: str,
        company: str,
        user_name: str,
        image_path: Optional[str] = None,
        email: Optional[str] = "",
        phone: Optional[str] = "",
        linkedin: Optional[str] = "",
    ):
        """Generate the PDF content (story)."""
        pass
