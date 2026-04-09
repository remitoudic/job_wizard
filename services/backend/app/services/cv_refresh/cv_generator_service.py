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
            flex-direction: column !important;
            align-items: center !important;
            padding: 40px 20px !important;
            margin: 0 !important;
            
            /* Scaling factor: Reverting to zoom as it preserves layout ratios better */
            zoom: 0.6 !important;
            -moz-transform: scale(0.6) !important;
            -moz-transform-origin: top center !important;

            /* Vertical Calibration: Prevent stretching */
            -webkit-font-smoothing: antialiased !important;
            -moz-osx-font-smoothing: grayscale !important;
            text-rendering: optimizeLegibility !important;
        }

        .cv-container {
            background-color: white !important;
            box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.25) !important;
            border: 1px solid #e2e8f0 !important;
            width: 210mm !important; /* Fixed A4 width */
            min-height: 297mm !important; /* A4 height */
            border-radius: 2px !important;
            position: relative !important;
            margin: 0 auto !important;
            
            /* Simulate @page margins for screen rendering */
            padding: 1.5cm !important; /* Classic standard align */
            box-sizing: border-box !important;

            /* ── PRO MAX: Sharp Cut Visualization ─────────────────────────── */
            /* This creates a very thin 2mm gap with strong shadows on both sides, */
            /* simulating stacked sheets of paper without hiding text. */
            background-image: 
                /* 1. Page Bottom Shadow */
                linear-gradient(to top, rgba(15,23,42,0.12) 0, transparent 4mm),
                /* 2. Page Top Shadow (for next page) */
                linear-gradient(to bottom, transparent 299mm, rgba(15,23,42,0.08) 300mm),
                /* 3. The physical 2mm Gap */
                linear-gradient(to bottom, #fff 297mm, #f1f5f9 297mm, #f1f5f9 299mm, #fff 299mm)
            !important;
            background-size: 100% 299mm !important; /* A4 297mm + 2mm Gap */
        }

        /* Dash overlay for the first page break - positioned precisely in the thin gap */
        .cv-container::after {
            content: "PAGE BREAK (A4)";
            position: absolute;
            top: 298mm; /* Exactly in the middle of the 2mm gap */
            left: 50%;
            transform: translate(-50%, -50%);
            background: #f1f5f9;
            padding: 1px 12px;
            border: 1px dashed #cbd5e1;
            border-radius: 99px;
            font-size: 8px;
            font-weight: 800;
            color: #64748b;
            letter-spacing: 0.12em;
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
                background-image: none !important;
            }
        }
    </style>
    <script>
        /**
         * Ultra-Calibrated Page-Break Reconciliation Script (Pro Max)
         * Forces the browser rendering to match WeasyPrint's tight PDF logic.
         */
        function reconcilePageBreaks() {
            // 1. Calibration: Measure pixel/mm ratio for THIS browser instance
            const ruler = document.createElement('div');
            ruler.style.height = '100mm';
            ruler.style.visibility = 'hidden';
            ruler.style.position = 'absolute';
            document.body.appendChild(ruler);
            const pxPerMm = ruler.offsetHeight / 100;
            document.body.removeChild(ruler);

            // 2. Safety Factor: WeasyPrint (PDF) renders ~1.5% tighter than browsers.
            // Applying a 0.985 factor synchronizes the vertical "trigger" points.
            const A4_HEIGHT_PX = (297 * pxPerMm) * 0.985;
            const GAP_HEIGHT_PX = 2 * pxPerMm;
            const totalCyclePx = A4_HEIGHT_PX + GAP_HEIGHT_PX;

            // Detect current scale factor (handles dynamic zoom)
            const container = document.querySelector('.cv-container');
            const scale = container.getBoundingClientRect().width / (210 * pxPerMm);
            const containerTop = container.getBoundingClientRect().top;

            const selectors = '.entry-item, .experience-item, .education-item, .skill-category, .section';
            
            function processCascade() {
                let shifted = false;
                const elements = document.querySelectorAll(selectors);
                
                for (let el of elements) {
                    // Reset to measure natural flow
                    const oldMargin = el.style.marginTop;
                    el.style.marginTop = '0';
                    
                    const rect = el.getBoundingClientRect();
                    const top = (rect.top - containerTop) / scale;
                    const bottom = (rect.bottom - containerTop) / scale;
                    
                    const pageOfTop = Math.floor(top / totalCyclePx);
                    const pageOfBottom = Math.floor(bottom / totalCyclePx);

                    if (pageOfTop !== pageOfBottom) {
                        const nextPageStart = (pageOfBottom * totalCyclePx);
                        const pushAmount = nextPageStart - top + 1; // +1px nudge
                        
                        if (pushAmount > 0 && pushAmount < (A4_HEIGHT_PX * 0.5)) {
                            el.style.marginTop = pushAmount + "px";
                            shifted = true;
                            break; // Stop and re-run entire cascade to handle shifted offsets
                        }
                    }
                }
                if (shifted) processCascade();
            }

            processCascade();
        }

        // Multiple triggers for stable rendering (font loading is async)
        window.addEventListener('load', reconcilePageBreaks);
        setTimeout(reconcilePageBreaks, 300);
        setTimeout(reconcilePageBreaks, 1500); // Final check for slow Type 1 fonts
    </script>
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
