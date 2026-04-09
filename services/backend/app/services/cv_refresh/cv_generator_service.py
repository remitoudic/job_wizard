"""
CV Generator Service — Renders CVData into a PDF using Jinja2 templates + WeasyPrint.
"""
import logging
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.services.cv_refresh.cv_parsers.cv_parser_service import CVData

logger = logging.getLogger("app.services.cv_refresh.cv_generator_service")

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

    def render_html(
        self,
        cv_data: CVData,
        template_name: str = "modern",
    ) -> str:
        """
        Render CV data to self-contained HTML (CSS inlined) for browser preview.

        Returns the full HTML string ready for iframe srcdoc injection.
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

        html_string = template.render(
            contact=cv_data.contact,
            summary=cv_data.summary,
            experiences=cv_data.experiences,
            education=cv_data.education,
            skills=cv_data.skills,
            languages=cv_data.languages,
        )

        # Inline CSS so the HTML is fully self-contained for iframe srcdoc
        if css_file.exists():
            css_content = css_file.read_text()
            style_tag = f"<style>{css_content}</style>"
            html_string = html_string.replace(
                f'<link rel="stylesheet" href="{template_name}.css">',
                style_tag,
            )

        # ── PREVIEW MODE STYLING ─────────────────────────────────────────────
        # Fixes scaling and aesthetics for the browser preview panel.
        # Uses 'zoom' (Chromium/Safari) and 'transform: scale' (Firefox) helper.
        # Forces a width of 210mm (A4) then scales down to fit the iframe.
        preview_styles = """
    <style>
        /* Override body for document-like preview */
        body {
            background-color: #f1f5f9 !important; /* slate-100 */
            display: flex !important;
            justify-content: center !important;
            padding: 40px 20px !important;
            margin: 0 !important;
            
            /* Aggressive scaling: 0.6 fits A4 height better into the 680px frame */
            zoom: 0.6;
            -moz-transform: scale(0.6);
            -moz-transform-origin: top center;
        }

        .cv-container {
            background-color: white !important;
            box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25) !important;
            border: 1px solid #e2e8f0 !important;
            width: 210mm !important; /* Fixed A4 width */
            min-height: 297mm !important; /* A4 height */
            border-radius: 2px !important;
            position: relative !important;
            
            /* Simulate @page margins for screen rendering */
            padding: 1.25cm 1.5cm !important;
            box-sizing: border-box !important;

            /* ── PRO MAX: Multi-page Visualization ─────────────────────────── */
            /* Draws a subtle dashed divider exactly every 297mm (A4 height) */
            background-image: repeating-linear-gradient(
                to bottom,
                transparent 0,
                transparent 296.8mm,
                #cbd5e1 296.8mm, /* slate-300 divider start */
                #cbd5e1 297mm,   /* slate-300 divider end */
                transparent 297mm
            ) !important;
            background-size: 100% 297mm !important;
        }

        /* Dash overlay for the page break */
        .cv-container::after {
            content: "PAGE BREAK INDICATOR (A4)";
            position: absolute;
            top: 297mm;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #f8fafc;
            padding: 2px 10px;
            border: 1px dashed #cbd5e1;
            border-radius: 99px;
            font-size: 9px;
            font-weight: 700;
            color: #94a3b8;
            letter-spacing: 0.05em;
            pointer-events: none;
            z-index: 10;
        }

        /* Prevent scroll jump on scale */
        html {
            overflow-x: hidden !important;
        }

        @media print {
            body { 
                zoom: 1 !important; 
                -moz-transform: none !important;
                background-color: white !important;
                padding: 0 !important;
            }
            .cv-container {
                box-shadow: none !important;
                border: none !important;
            }
        }
    </style>
"""
        # Inject just before </body>
        if "</body>" in html_string:
            html_string = html_string.replace("</body>", f"{preview_styles}</body>")
        else:
            html_string += preview_styles

        return html_string

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
