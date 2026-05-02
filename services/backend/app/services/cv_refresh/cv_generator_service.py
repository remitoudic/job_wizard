"""
CV Generator Service — Renders CVData into a PDF using Jinja2 templates + WeasyPrint.
"""
import logging
import re
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.services.cv_refresh.cv_parsers.cv_parser_service import CVData

logger = logging.getLogger("app.services.cv_refresh.cv_generator_service")

# Template directory lives alongside this file
TEMPLATES_DIR = Path(__file__).parent / "cv_templates"

# A4 dimensions in mm
A4_HEIGHT_MM = 297
A4_WIDTH_MM = 210


def _parse_page_margins(css_content: str) -> dict[str, float]:
    """Extract @page margin values from template CSS.

    Returns a dict with top/right/bottom/left margins in cm.
    Defaults to 1.5cm all sides if not found.
    """
    default = {"top": 1.5, "right": 1.5, "bottom": 1.5, "left": 1.5}

    page_match = re.search(r"@page\s*\{([^}]+)\}", css_content)
    if not page_match:
        return default

    block = page_match.group(1)
    margin_match = re.search(r"margin:\s*([^;]+);", block)
    if not margin_match:
        return default

    raw = margin_match.group(1).strip()
    parts = raw.split()

    def _to_cm(val: str) -> float:
        val = val.strip()
        if val.endswith("cm"):
            return float(val.replace("cm", ""))
        if val.endswith("mm"):
            return float(val.replace("mm", "")) / 10.0
        return 1.5  # fallback

    if len(parts) == 1:
        v = _to_cm(parts[0])
        return {"top": v, "right": v, "bottom": v, "left": v}
    elif len(parts) == 2:
        tb, lr = _to_cm(parts[0]), _to_cm(parts[1])
        return {"top": tb, "right": lr, "bottom": tb, "left": lr}
    elif len(parts) == 3:
        t, lr, b = _to_cm(parts[0]), _to_cm(parts[1]), _to_cm(parts[2])
        return {"top": t, "right": lr, "bottom": b, "left": lr}
    elif len(parts) >= 4:
        return {
            "top": _to_cm(parts[0]),
            "right": _to_cm(parts[1]),
            "bottom": _to_cm(parts[2]),
            "left": _to_cm(parts[3]),
        }
    return default


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
        Includes visual page break indicators matching the PDF @page rules.
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
        css_content = ""
        if css_file.exists():
            css_content = css_file.read_text()
            style_tag = f"<style>{css_content}</style>"
            html_string = html_string.replace(
                f'<link rel="stylesheet" href="{template_name}.css">',
                style_tag,
            )

        # ── Parse @page margins for accurate page break positions ─────────
        margins = _parse_page_margins(css_content)
        margin_top_cm = margins["top"]
        margin_bottom_cm = margins["bottom"]
        page_padding_cm = margin_top_cm  # Preview uses top margin as padding

        # Full A4 page height in mm
        full_page_mm = A4_HEIGHT_MM
        # Content area per page (inside @page margins)
        content_height_mm = A4_HEIGHT_MM - (margin_top_cm + margin_bottom_cm) * 10

        # ── PREVIEW MODE STYLING ─────────────────────────────────────────────
        # Simulates A4 pages with visual break indicators.
        # The .cv-container padding mirrors the @page margins so content
        # flows at the same width/position as in the PDF.
        # A repeating background gradient draws a dashed line every page height.
        preview_styles = f"""
    <style>
        /* Override body for document-like preview */
        body {{
            background-color: #f1f5f9 !important; /* slate-100 */
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            padding: 40px 20px !important;
            margin: 0 !important;

            /* Scaling factor: zoom preserves layout ratios better */
            zoom: 0.6 !important;
            -moz-transform: scale(0.6) !important;
            -moz-transform-origin: top center !important;

            /* Vertical Calibration */
            -webkit-font-smoothing: antialiased !important;
            -moz-osx-font-smoothing: grayscale !important;
            text-rendering: optimizeLegibility !important;
        }}

        .cv-container {{
            background-color: white !important;
            box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25) !important;
            border: 1px solid #e2e8f0 !important;
            width: {A4_WIDTH_MM}mm !important; /* Fixed A4 width */
            min-height: {A4_HEIGHT_MM}mm !important; /* A4 height */
            border-radius: 2px !important;
            position: relative !important;
            margin: 0 auto !important;

            /* Simulate @page margins for screen rendering */
            padding: {page_padding_cm}cm !important;
            box-sizing: border-box !important;
            pointer-events: none;
            z-index: 10;

            /* ── Page break indicator ──────────────────────────────
               Repeating gradient draws a dashed line every full page.
               Position: at the bottom of each page's content area,
               which is every {A4_HEIGHT_MM}mm from the top of the container
               (since container padding = @page margin). */
            background-image:
                repeating-linear-gradient(
                    to bottom,
                    transparent 0mm,
                    transparent calc({full_page_mm}mm - 12px),
                    transparent calc({full_page_mm}mm - 12px),
                    #f1f5f9 calc({full_page_mm}mm - 12px),
                    #f1f5f9 calc({full_page_mm}mm + 12px),
                    transparent calc({full_page_mm}mm + 12px)
                ) !important;
            background-size: 100% {full_page_mm}mm !important;
            background-repeat: repeat-y !important;
        }}

        /* ── Page break separator label ──────────────────────── */
        .page-break-marker {{
            width: 100%;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            pointer-events: none;
            margin: 0;
            padding: 0;
        }}

        .page-break-marker::before {{
            content: '';
            position: absolute;
            left: -{ page_padding_cm }cm;
            right: -{ page_padding_cm }cm;
            top: 50%;
            height: 0;
            border-top: 1.5px dashed #94a3b8; /* slate-400 */
        }}

        .page-break-marker span {{
            position: relative;
            z-index: 2;
            background: #f1f5f9;
            color: #64748b; /* slate-500 */
            font-size: 7.5pt;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            padding: 2px 12px;
            border-radius: 10px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            white-space: nowrap;
        }}

        /* Prevent scroll jump on scale */
        html {{
            overflow-x: hidden !important;
        }}

        @media print {{
            body {{
                zoom: 1 !important;
                -moz-transform: none !important;
                background-color: white !important;
                padding: 0 !important;
            }}
            .cv-container {{
                box-shadow: none !important;
                border: none !important;
                background-image: none !important;
            }}
            .page-break-marker {{
                display: none !important;
            }}
        }}
    </style>
"""

        # ── Page count estimation script ──────────────────────────────────
        # Runs inside the iframe after content loads.
        # Calculates how many pages the CV would span and:
        # 1. Sets document.title to "pages:N" so the parent frame can read it
        # 2. Injects visual page-break marker divs at each page boundary
        page_script = f"""
    <script>
        (function() {{
            var PAGE_H = {content_height_mm};  // content height per page in mm
            var FULL_PAGE_H = {full_page_mm};  // full page height in mm
            var MM_TO_PX = 3.7795275591;       // 1mm = 96/25.4 px

            function init() {{
                var container = document.querySelector('.cv-container');
                if (!container) return;

                var contentH = container.scrollHeight;
                var pageHpx = FULL_PAGE_H * MM_TO_PX;
                var pages = Math.max(1, Math.ceil(contentH / pageHpx));

                document.title = 'pages:' + pages;

                // Insert visual page-break markers at each boundary
                // We walk through the container's direct children and find
                // elements that cross a page boundary, inserting a marker before them.
                if (pages <= 1) return;

                // Collect all page break Y positions (relative to container top)
                var breakPoints = [];
                for (var i = 1; i < pages; i++) {{
                    breakPoints.push(i * pageHpx);
                }}

                // Get all block-level children recursively at section level
                var sections = container.querySelectorAll('.section, .experience-item, .education-item, .entry-item, .timeline-item, .cv-header, .cv-body');
                if (!sections.length) return;

                var containerTop = container.getBoundingClientRect().top + window.scrollY;

                breakPoints.forEach(function(bp, idx) {{
                    // Find the first element that starts at or after this break point
                    var bestEl = null;
                    var bestDist = Infinity;

                    sections.forEach(function(el) {{
                        var elTop = el.getBoundingClientRect().top + window.scrollY - containerTop;
                        // Find element closest to (but after) the break point
                        if (elTop >= bp - 20 && elTop < bp + pageHpx * 0.5) {{
                            var dist = Math.abs(elTop - bp);
                            if (dist < bestDist) {{
                                bestDist = dist;
                                bestEl = el;
                            }}
                        }}
                    }});

                    // Create the marker
                    var marker = document.createElement('div');
                    marker.className = 'page-break-marker';
                    marker.innerHTML = '<span>Page ' + (idx + 2) + '</span>';

                    if (bestEl && bestEl.parentNode) {{
                        bestEl.parentNode.insertBefore(marker, bestEl);
                    }}
                }});

                // Recalculate page count after markers are inserted
                var finalH = container.scrollHeight;
                var finalPages = Math.max(1, Math.ceil(finalH / pageHpx));
                document.title = 'pages:' + finalPages;
            }}

            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', init);
            }} else {{
                init();
            }}
        }})();
    </script>
"""

        # Inject preview styles + script just before </body>
        inject_content = preview_styles + page_script
        if "</body>" in html_string:
            html_string = html_string.replace("</body>", f"{inject_content}</body>")
        else:
            html_string += inject_content

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
