from typing import List, Optional, Dict
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

from .base import BaseTemplate
from .registry import TemplateRegistry

# French month names
_FR_MONTHS = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


def _format_french_date(date_str: str) -> str:
    """Format a date string as French: '11 avril 2026'."""
    try:
        dt = datetime.strptime(date_str, "%d %B %Y")
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            return date_str  # Return as-is if unparseable
    return f"{dt.day} {_FR_MONTHS[dt.month - 1]} {dt.year}"


class FrenchTemplate(BaseTemplate):
    """
    French cover letter template (Lettre de Motivation).
    Layout order:
      1. Sender block (top-left): Name, Address, Contact
      2. Recipient block (top-right, offset down): Recipient name, Company, Address
      3. Place and Date (right-aligned): "À [City], le [Date]"
      4. Subject line (Objet) — bold, left
      5. Body
    Margins: Left 2.5 cm, Right 2.5 cm, Top 3.0 cm, Bottom 2.5 cm
    Font: Helvetica (sans-serif)
    """

    def get_margins(self) -> Dict[str, float]:
        """Standard professional margins (reduced top margin)."""
        return {
            "leftMargin": 2.5 * cm,
            "rightMargin": 2.5 * cm,
            "topMargin": 2.0 * cm,
            "bottomMargin": 2.5 * cm,
        }

    def _setup_custom_styles(self):
        """Override styles with Helvetica (sans-serif)."""
        from reportlab.lib.styles import getSampleStyleSheet

        self.styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            "FrenchTitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=HexColor("#1a1a1a"),
            spaceAfter=2,
            alignment=TA_LEFT,
        )
        self.header_style = ParagraphStyle(
            "FrenchHeader",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=HexColor("#1a1a1a"),
            leading=12,
            spaceAfter=1,
            alignment=TA_LEFT,
        )
        self.recipient_style = ParagraphStyle(
            "FrenchRecipient",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            textColor=HexColor("#000000"),
            leading=14,
            alignment=TA_LEFT,
            leftIndent=3.0 * inch,  # Offset to the right
        )
        self.body_style = ParagraphStyle(
            "FrenchBody",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            textColor=HexColor("#1a1a1a"),
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=12,
        )
        self.subject_style = ParagraphStyle(
            "FrenchSubject",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=HexColor("#1a1a1a"),
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

        # Address line
        if address_street:
            story.append(Paragraph(address_street, self.header_style))
            city_line = f"{address_postcode} {address_city}".strip()
            if address_country:
                city_line += f", {address_country}"
            story.append(Paragraph(city_line, self.header_style))
        elif address:
            story.append(Paragraph(address, self.header_style))

        # Contact line
        if phone:
            story.append(Paragraph(phone, self.header_style))
        if email:
            story.append(Paragraph(email, self.header_style))

        story.append(Spacer(1, 0.4 * inch))

        # 2. Recipient block (right side, slightly lower)
        if recipient_name or company or employer_address:
            if recipient_name:
                story.append(Paragraph(recipient_name, self.recipient_style))
            if company:
                story.append(Paragraph(f"<b>{company}</b>", self.recipient_style))
            if employer_address:
                for line in employer_address.split("\n"):
                    if line.strip():
                        story.append(Paragraph(line.strip(), self.recipient_style))
            story.append(Spacer(1, 0.4 * inch))

        # 3. Date — right-aligned, French format
        if custom_date is None:
            now = datetime.now()
            raw_date = now.strftime("%d %B %Y")
        else:
            raw_date = custom_date

        if raw_date:
            french_date = _format_french_date(raw_date)
            # Add city if available
            city_prefix = f"À {address_city}, le " if address_city else "Le "
            full_date_string = f"{city_prefix}{french_date}"

            date_style = ParagraphStyle(
                "FrenchDate",
                parent=self.body_style,
                alignment=TA_RIGHT,
            )
            story.append(Paragraph(full_date_string, date_style))
            story.append(Spacer(1, 0.4 * inch))

        # 4. Subject line (Objet)
        if custom_subject is None:
            subject_text = f"Objet : Candidature au poste de {job_title}"
        else:
            subject_text = custom_subject

        if subject_text:
            story.append(Paragraph(subject_text, self.subject_style))
            story.append(Spacer(1, 0.3 * inch))

        # 5. Body
        self._add_paragraphs(story, cover_letter)


# Register the template
TemplateRegistry.register("french", FrenchTemplate)
