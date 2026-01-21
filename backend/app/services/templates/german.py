from typing import List, Optional
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.colors import HexColor

from .base import BaseTemplate
from .registry import TemplateRegistry

class GermanTemplate(BaseTemplate):
    """
    German style template (DIN 5008 inspired).
    Layout:
    - Header: distinct style
    - Date: Right aligned
    - Subject: Bold
    """

    def generate(
        self,
        doc: SimpleDocTemplate,
        story: List,
        cover_letter: str,
        job_title: str,
        company: str,
        user_name: str,
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
        # 1. Header (Standard 3-line format)
        display_name = full_name if full_name else user_name
        if not full_name and (first_name or surname):
            display_name = f"{first_name} {surname}".strip()
        
        # Line 1: Name
        if display_name:
            story.append(Paragraph(display_name, self.title_style))

        # Line 2: Address (Street, Postcode City Country)
        addr_line = ""
        if address_street:
            city_line = f"{address_postcode} {address_city}".strip()
            addr_line = f"{address_street}, {city_line}"
            if address_country:
                addr_line += f", {address_country}"
        elif address:
            addr_line = address
        
        if addr_line:
            story.append(Paragraph(addr_line, self.header_style))

        # Line 3: Email | Phone | LinkedIn
        contact_parts = []
        if email: contact_parts.append(email)
        if phone: contact_parts.append(phone)
        if linkedin: contact_parts.append(linkedin)
        
        if contact_parts:
            story.append(Paragraph(" | ".join(contact_parts), self.header_style))
            
        story.append(Spacer(1, 0.4 * inch))
        
        # 2. Date (Right Side)
        # German format: Day. Month Year
        # Fallback to current date only if custom_date is None, but skip if it's an empty string
        current_date = datetime.now().strftime("%d. %B %Y") if custom_date is None else custom_date
        
        if current_date:
            date_style = ParagraphStyle('DateStyle', parent=self.body_style, alignment=TA_RIGHT)
            story.append(Paragraph(current_date, date_style))
            story.append(Spacer(1, 0.2 * inch))

        # 3. Subject (Left Side) - Bold
        # Fallback to default Re: line only if custom_subject is None, but skip if it's an empty string
        if custom_subject is None:
             subject_text = f"<b>Re: Application for {job_title} at {company}</b>"
        else:
             subject_text = f"<b>{custom_subject}</b>" if custom_subject else ""

        if subject_text:
            subject_style = self.subtitle_style
            subject_style.alignment = TA_LEFT
            story.append(Paragraph(subject_text, subject_style))
            story.append(Spacer(1, 0.2 * inch))

        # 4. User Photo 
        if image_path:
             self._add_user_photo(story, image_path)

        # 5. Body
        self._add_paragraphs(story, cover_letter)

# Register the template
TemplateRegistry.register("german", GermanTemplate)
