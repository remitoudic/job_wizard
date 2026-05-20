from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate
from typing import Optional
import logfire


class PDFService:
    """Service for generating PDF cover letters"""

    def __init__(self):
        self.page_width, self.page_height = A4

    def _sanitize_text(self, text: Optional[str]) -> Optional[str]:
        """Replace Unicode characters that ReportLab's standard fonts can't render."""
        if not text:
            return text
        replacements = {
            "\u2013": "-",  # en dash
            "\u2014": "-",  # em dash
            "\u2011": "-",  # non-breaking hyphen
            "\u2018": "'",  # left single quote
            "\u2019": "'",  # right single quote
            "\u201c": '"',  # left double quote
            "\u201d": '"',  # right double quote
            "\u2022": "-",  # bullet
            "\u2026": "...",  # ellipsis
            "\u202f": " ",  # narrow no-break space
            "\u00a0": " ",  # no-break space
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

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
        Margins are determined by the template (e.g. DIN 5008 for German).
        """
        # Get template strategy first — margins depend on it
        from app.services.cover_letter.templates import TemplateRegistry

        template = TemplateRegistry.get(template_name)

        # Build document with template-specific margins
        margins = template.get_margins()
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            **margins,
        )

        # Prepare story container
        story = []

        # Delegate generation to strategy
        template.generate(
            doc=doc,
            story=story,
            cover_letter=self._sanitize_text(cover_letter),
            job_title=self._sanitize_text(job_title),
            company=self._sanitize_text(company),
            user_name=self._sanitize_text(user_name),
            first_name=self._sanitize_text(first_name),
            surname=self._sanitize_text(surname),
            image_path=image_path,
            email=self._sanitize_text(email),
            phone=self._sanitize_text(phone),
            linkedin=self._sanitize_text(linkedin),
            custom_date=self._sanitize_text(custom_date),
            custom_subject=self._sanitize_text(custom_subject),
            full_name=self._sanitize_text(full_name),
            address=self._sanitize_text(address),
            address_street=self._sanitize_text(address_street),
            address_postcode=self._sanitize_text(address_postcode),
            address_city=self._sanitize_text(address_city),
            address_country=self._sanitize_text(address_country),
            employer_address=self._sanitize_text(employer_address),
            recipient_name=self._sanitize_text(recipient_name),
        )

        # Build PDF
        try:
            logfire.info("Generating PDF", template=template_name, output=output_path)
            doc.build(story)
        except Exception as e:
            logfire.error("PDF generation failed", error=str(e))
            raise e
