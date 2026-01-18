from typing import List, Optional
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.colors import HexColor

from .base import BaseTemplate
from .registry import TemplateRegistry

class GenericTemplate(BaseTemplate):
    """
    Generic/Standard template.
    Layout:
    - Header (Left): Name & Contact
    - Date (Left): Below header
    - Subject (Right): Below date
    - Body: Standard
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
    ):
        # 1. Header (Left Side)
        # Name - use first_name and surname if provided, otherwise fall back to user_name
        display_name = user_name
        if first_name or surname:
            display_name = f"{first_name} {surname}".strip()
        
        name_style = self.title_style
        name_style.alignment = TA_LEFT
        story.append(Paragraph(display_name, name_style))
        story.append(Spacer(1, 0.05 * inch))

        # Contact Info (Left)
        contact_parts = []
        if email: contact_parts.append(email)
        if phone: contact_parts.append(phone)
        if linkedin: contact_parts.append(linkedin)
        
        if contact_parts:
            # Join with separators or put on new lines?
            # User request: "flexible... flexible header on left side"
            # Let's stack them for clarity on the left
            contact_style = self.contact_style
            contact_style.alignment = TA_LEFT
            for part in contact_parts:
                story.append(Paragraph(part, contact_style))
            story.append(Spacer(1, 0.2 * inch))
        
        # 2. Date (Right Side)
        current_date = datetime.now().strftime("%B %d, %Y")
        date_style = self.body_style
        date_style.alignment = TA_RIGHT
        story.append(Paragraph(current_date, date_style))
        story.append(Spacer(1, 0.2 * inch))

        # 3. Subject (Left Side)
        subject_text = f"Re: Application for {job_title} at {company}"
        subject_style = self.subtitle_style
        subject_style.alignment = TA_LEFT
        story.append(Paragraph(subject_text, subject_style))
        story.append(Spacer(1, 0.3 * inch))

        # 4. User Photo (Optional - where to put it given the layout?)
        # Base implementation puts it in story. If called here, it appends.
        # Let's put it at the very top if exists, or maybe skip for this specific "Text-heavy" layout?
        # The user didn't specify photo position in this new request. 
        # But previous "Personalization" feature allowed photo.
        # Let's add it at the top-right perhaps? Or just standard top center?
        # For now, let's keep it simple and append it if provided, but maybe before header?
        # Actually, let's stick to the base helper but maybe customize position if needed.
        # Since the user emphasized the text layout, I'll put the image at the top-right or just top-centered before everything.
        # Let's use the base helper at the start.
        if image_path:
             self._add_user_photo(story, image_path)

        # 5. Body
        self._add_paragraphs(story, cover_letter)

# Register the template
TemplateRegistry.register("generic", GenericTemplate)
