from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from PIL import Image as PILImage
import os
import re
import unicodedata


# Unicode → Latin-1 safe replacement map.
# ReportLab's built-in fonts only support Latin-1; unsupported codepoints
# render as black boxes (tofu). This map normalises them to safe equivalents.
_UNICODE_REPLACEMENTS = {
    # Hyphens and dashes
    "\u2010": "-",  # HYPHEN
    "\u2011": "-",  # NON-BREAKING HYPHEN
    "\u2012": "-",  # FIGURE DASH
    "\u2013": "-",  # EN DASH
    "\u2014": "-",  # EM DASH  (use '--' if you prefer)
    "\u2015": "-",  # HORIZONTAL BAR
    "\u00ad": "",  # SOFT HYPHEN (invisible, remove)
    "\ufe63": "-",  # SMALL HYPHEN-MINUS
    "\uff0d": "-",  # FULLWIDTH HYPHEN-MINUS
    # Quotation marks
    "\u2018": "'",  # LEFT SINGLE QUOTATION MARK
    "\u2019": "'",  # RIGHT SINGLE QUOTATION MARK
    "\u201a": "'",  # SINGLE LOW-9 QUOTATION MARK
    "\u201b": "'",  # SINGLE HIGH-REVERSED-9 QUOTATION MARK
    "\u201c": '"',  # LEFT DOUBLE QUOTATION MARK
    "\u201d": '"',  # RIGHT DOUBLE QUOTATION MARK
    "\u201e": '"',  # DOUBLE LOW-9 QUOTATION MARK
    "\u201f": '"',  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
    "\u00ab": '"',  # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    "\u00bb": '"',  # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
    # Spaces / invisible characters
    "\u200b": "",  # ZERO WIDTH SPACE
    "\u200c": "",  # ZERO WIDTH NON-JOINER
    "\u200d": "",  # ZERO WIDTH JOINER
    "\ufeff": "",  # BYTE ORDER MARK / ZERO WIDTH NO-BREAK SPACE
    "\u00a0": " ",  # NON-BREAKING SPACE → regular space
    "\u2002": " ",  # EN SPACE
    "\u2003": " ",  # EM SPACE
    "\u2009": " ",  # THIN SPACE
    "\u202f": " ",  # NARROW NO-BREAK SPACE
    # Dots / ellipsis
    "\u2026": "...",  # HORIZONTAL ELLIPSIS
    "\u2022": "-",  # BULLET
    "\u2023": ">",  # TRIANGULAR BULLET
    "\u2043": "-",  # HYPHEN BULLET
    # Misc
    "\u2032": "'",  # PRIME
    "\u2033": '"',  # DOUBLE PRIME
    "\u2044": "/",  # FRACTION SLASH
}

# Pre-compiled regex for all keys
_UNICODE_PATTERN = re.compile("|".join(re.escape(k) for k in _UNICODE_REPLACEMENTS))


class BaseTemplate(ABC):
    """Abstract base class for cover letter PDF templates."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Replace Unicode characters unsupported by ReportLab built-in fonts.

        Built-in PDF fonts (Helvetica, Times-Roman, Courier) only cover
        Latin-1 (ISO 8859-1). Characters outside that range — commonly
        produced by LLMs — appear as black boxes. This method normalises
        them to safe ASCII/Latin-1 equivalents while preserving valid
        Latin-1 characters (German umlauts, French accents, etc.).
        """
        if not text:
            return text

        # Fast-path: apply known replacements via single regex pass
        result = _UNICODE_PATTERN.sub(lambda m: _UNICODE_REPLACEMENTS[m.group()], text)

        # Fallback: handle any remaining non-Latin-1 characters.
        # Process character-by-character: keep Latin-1 chars as-is,
        # attempt NFKD decomposition for ligatures (e.g. ﬁ → fi),
        # and silently drop anything else.
        cleaned = []
        for ch in result:
            try:
                ch.encode("latin-1")
                cleaned.append(ch)
            except UnicodeEncodeError:
                # Try NFKD decomposition (handles ligatures like ﬁ → fi)
                decomposed = unicodedata.normalize("NFKD", ch)
                for sub_ch in decomposed:
                    try:
                        sub_ch.encode("latin-1")
                        cleaned.append(sub_ch)
                    except UnicodeEncodeError:
                        pass  # Drop truly unsupported characters

        return "".join(cleaned)

    def get_margins(self) -> Dict[str, float]:
        """Return page margins. Override in subclasses for non-standard formats."""
        margin = 0.75 * inch
        return {
            "leftMargin": margin,
            "rightMargin": margin,
            "topMargin": margin,
            "bottomMargin": margin,
        }

    def _setup_custom_styles(self):
        """Define custom paragraph styles."""
        # Clean defaults to avoid pollution
        self.title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Normal"],
            fontName="Times-Bold",
            fontSize=11,
            textColor=HexColor("#1a1a1a"),
            spaceAfter=2,
            alignment=TA_LEFT,
        )
        self.header_style = ParagraphStyle(
            "CustomHeader",
            parent=self.styles["Normal"],
            fontName="Times-Roman",
            fontSize=11,
            textColor=HexColor("#1a1a1a"),
            leading=14,
            spaceAfter=2,
            alignment=TA_LEFT,
        )
        self.body_style = ParagraphStyle(
            "CustomBody",
            parent=self.styles["Normal"],
            fontName="Times-Roman",
            fontSize=11,
            textColor=HexColor("#1a1a1a"),
            leading=16,
            alignment=TA_LEFT,
            spaceAfter=12,
        )
        self.subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=self.styles["Normal"],
            fontName="Times-Bold",
            fontSize=11,
            textColor=HexColor("#1a1a1a"),
            leading=14,
            spaceAfter=4,
            alignment=TA_LEFT,
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
                photo.hAlign = "CENTER"  # Default to center, templates can override
                story.append(photo)
                story.append(Spacer(1, 0.3 * inch))
            except Exception as e:
                print(f"Warning: Could not add image to PDF: {e}")

    def _add_paragraphs(self, story: List, text: str):
        """Helper to add cover letter body paragraphs."""
        # Sanitize text to remove unsupported Unicode characters
        text = self.sanitize_text(text)
        # Split by double newlines for actual paragraph spacing
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            if para.strip():
                # Replace single newlines with br tags to preserve line breaks within paragraphs
                para_text = para.strip().replace("\n", "<br/>")
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
        """Generate the PDF content (story)."""
        pass
