"""
CV Generator Service — Renders CVData into a PDF using Jinja2 templates + WeasyPrint.
"""
import logging
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.services.cv_parser_service import CVData

logger = logging.getLogger("app.services.cv_generator_service")

# Template directory lives alongside this file
TEMPLATES_DIR = Path(__file__).parent / "cv_templates"


class CVTemplate:
    """Metadata about an available CV template."""

    def __init__(self, name: str, label: str, description: str):
        self.name = name
        self.label = label
        self.description = description

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
        }


class CVGeneratorService:
    """Generate a PDF CV from structured CVData and a Jinja2 template."""

    def __init__(self):
        self._env: Optional[Environment] = None

    @property
    def env(self) -> Environment:
        if self._env is None:
            self._env = Environment(
                loader=FileSystemLoader(str(TEMPLATES_DIR)),
                autoescape=True,
            )
        return self._env

    # ── Public API ───────────────────────────────────────────────────────

    def list_templates(self) -> list[CVTemplate]:
        """Discover available templates by scanning the cv_templates directory."""
        templates: list[CVTemplate] = []
        if not TEMPLATES_DIR.exists():
            return templates

        for html_file in sorted(TEMPLATES_DIR.glob("*.html")):
            name = html_file.stem
            # Read optional description from a companion .txt file
            desc_file = TEMPLATES_DIR / f"{name}.txt"
            description = ""
            if desc_file.exists():
                description = desc_file.read_text().strip()

            templates.append(
                CVTemplate(
                    name=name,
                    label=name.replace("_", " ").title(),
                    description=description or f"{name.title()} CV template",
                )
            )
        return templates

    def generate_pdf(
        self,
        cv_data: CVData,
        template_name: str = "modern",
        output_path: Optional[str] = None,
    ) -> bytes:
        """
        Render the CV as a PDF.

        Args:
            cv_data: Structured CV data.
            template_name: Name of the template (without extension).
            output_path: If provided, write the PDF to this file path.

        Returns:
            The raw PDF bytes.
        """
        template_file = f"{template_name}.html"
        css_file = TEMPLATES_DIR / f"{template_name}.css"

        if not (TEMPLATES_DIR / template_file).exists():
            available = [t.name for t in self.list_templates()]
            raise ValueError(
                f"Template '{template_name}' not found. "
                f"Available: {available}"
            )

        template = self.env.get_template(template_file)

        # Render HTML
        html_string = template.render(
            contact=cv_data.contact,
            summary=cv_data.summary,
            experiences=cv_data.experiences,
            education=cv_data.education,
            skills=cv_data.skills,
            languages=cv_data.languages,
        )

        # Build CSS list
        stylesheets = []
        if css_file.exists():
            from weasyprint import CSS
            stylesheets.append(CSS(filename=str(css_file)))

        # Generate PDF
        logger.info(f"Generating CV PDF with template '{template_name}'")
        html = HTML(string=html_string, base_url=str(TEMPLATES_DIR))
        pdf_bytes = html.write_pdf(stylesheets=stylesheets)

        if output_path:
            Path(output_path).write_bytes(pdf_bytes)
            logger.info(f"PDF written to {output_path}")

        return pdf_bytes


# Module-level singleton
cv_generator_service = CVGeneratorService()
