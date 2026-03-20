from typing import List, Optional, Dict
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

from .base import BaseTemplate
from .registry import TemplateRegistry

# German month names for DIN 5008 date formatting
_DE_MONTHS = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]


def _format_german_date(date_str: str) -> str:
    """Format a date string as German DIN 5008: '16. März 2026'."""
    try:
        dt = datetime.strptime(date_str, "%d %B %Y")
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            return date_str  # Return as-is if unparseable
    return f"{dt.day}. {_DE_MONTHS[dt.month - 1]} {dt.year}"


class GermanTemplate(BaseTemplate):
    """
    German cover letter template — DIN 5008 standard (Bewerbungsschreiben).
    Layout order:
      1. Sender block (top-left): Name, Address, Contact
      2. Recipient block (left): Recipient name, Company, Address
      3. Date (right-aligned)
      4. Subject line (Betreff) — bold, left, no period at end
      5. Body
    Margins: Left 2.5 cm, Right 2.0 cm, Top 4.5 cm, Bottom 2.0 cm (DIN 5008)
    Font: Helvetica (sans-serif, standard for German business letters)
    """

    def get_margins(self) -> Dict[str, float]:
        """DIN 5008 standard margins."""
        return {
            "leftMargin": 2.5 * cm,
            "rightMargin": 2.0 * cm,
            "topMargin": 4.5 * cm,
            "bottomMargin": 2.0 * cm,
        }

    def _setup_custom_styles(self):
        """Override styles with Helvetica (sans-serif) for German standard."""
        from reportlab.lib.styles import getSampleStyleSheet
        self.styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            'GermanTitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=2,
            alignment=TA_LEFT,
        )
        self.header_style = ParagraphStyle(
            'GermanHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            textColor=HexColor('#1a1a1a'),
            leading=14,
            spaceAfter=1,
            alignment=TA_LEFT,
        )
        self.body_style = ParagraphStyle(
            'GermanBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            textColor=HexColor('#1a1a1a'),
            leading=16,
            alignment=TA_LEFT,
            spaceAfter=12,
        )
        self.subtitle_style = ParagraphStyle(
            'GermanSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=HexColor('#1a1a1a'),
            leading=14,
            spaceAfter=4,
            alignment=TA_LEFT,
        )

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
        # 1. Sender block (top-left)
        display_name = full_name if full_name else user_name
        if not full_name and (first_name or surname):
            display_name = f"{first_name} {surname}".strip()

        if display_name:
            story.append(Paragraph(display_name, self.title_style))

        # Address line: "Musterstraße 1, 10115 Berlin"
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

        # Contact line: phone | email | linkedin
        contact_parts = []
        if phone: contact_parts.append(phone)
        if email: contact_parts.append(email)
        if linkedin: contact_parts.append(linkedin)

        if contact_parts:
            story.append(Paragraph(" | ".join(contact_parts), self.header_style))

        story.append(Spacer(1, 0.5 * inch))

        # 2. Recipient block (left) — DIN 5008: recipient before date
        if recipient_name or company or employer_address:
            if recipient_name:
                story.append(Paragraph(recipient_name, self.header_style))
            if company:
                story.append(Paragraph(company, self.header_style))
            if employer_address:
                for line in employer_address.split('\n'):
                    if line.strip():
                        story.append(Paragraph(line.strip(), self.header_style))
            story.append(Spacer(1, 0.3 * inch))

        # 3. Date — right-aligned, German format (DIN 5008)
        if custom_date is None:
            now = datetime.now()
            raw_date = now.strftime("%d %B %Y")
        else:
            raw_date = custom_date

        if raw_date:
            german_date = _format_german_date(raw_date)
            date_style = ParagraphStyle(
                'GermanDate',
                parent=self.body_style,
                alignment=TA_RIGHT,
            )
            story.append(Paragraph(german_date, date_style))
            story.append(Spacer(1, 0.3 * inch))

        # 4. Subject line (Betreff) — bold, no period at end (DIN 5008)
        if custom_subject is None:
            subject_text = f"<b>Bewerbung als {job_title}</b>"
        else:
            subject_text = f"<b>{custom_subject}</b>" if custom_subject else ""

        if subject_text:
            story.append(Paragraph(subject_text, self.subtitle_style))
            story.append(Spacer(1, 0.3 * inch))

        # 5. Optional photo (after header, before body — per DIN 5008)
        if image_path:
            self._add_user_photo(story, image_path)

        # 6. Body
        self._add_paragraphs(story, cover_letter)


# Register the template
TemplateRegistry.register("german", GermanTemplate)
