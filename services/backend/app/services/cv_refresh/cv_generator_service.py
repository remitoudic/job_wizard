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
         * Ultra-Calibrated Page-Break Reconciliation Script (v2.1 - High Stability)
         * Forces the browser rendering to match WeasyPrint's tight PDF logic.
         */
        function reconcilePageBreaks() {
            console.log("[CV Preview] Calibration Triggered");
            const container = document.querySelector('.cv-container');
            if (!container) return;

            // 1. Internal Calibration: Measure px/mm INSIDE the container to bake in zoom/scaling
            const ruler = document.createElement('div');
            ruler.style.cssText = 'height:100mm; width:1px; position:absolute; visibility:hidden; pointer-events:none;';
            container.appendChild(ruler);
            const pxPerMm = ruler.offsetHeight / 100;
            container.removeChild(ruler);

            // 2. Constants: Must align EXACTLY with the CSS background-size (299mm)
            const A4_HEIGHT_MM = 297;
            const GAP_HEIGHT_MM = 2;
            const TOTAL_CYCLE_MM = A4_HEIGHT_MM + GAP_HEIGHT_MM; // 299mm
            
            // 3. Precision Threshold: 0.980 (6mm safety buffer) 
            const TRIGGER_THRESHOLD_MM = A4_HEIGHT_MM * 0.980; 

            const TOTAL_CYCLE_PX = TOTAL_CYCLE_MM * pxPerMm;
            const THRESHOLD_PX = TRIGGER_THRESHOLD_MM * pxPerMm;

            const containerTop = container.getBoundingClientRect().top;
            const containerWidth = container.getBoundingClientRect().width;
            const scale = containerWidth / (210 * pxPerMm);

            // Selectors for Atomic Blocks (Tracking entries and headers across all templates)
            // Note: We avoid tracking 'section.section' here because it is a container that SHOULD be able to split across pages.
            const selectors = '.experience-item, .education-item, .skill-category, h2, h3, .entry-item, .timeline-item';
            
            function processSinglePass() {
                const elements = Array.from(document.querySelectorAll(selectors));
                
                // Reset all first to find pure natural flow
                elements.forEach(el => el.style.marginTop = '0');

                elements.forEach((el, i) => {
                    const rect = el.getBoundingClientRect();
                    const top = (rect.top - containerTop) / scale;
                    const height = (rect.height) / scale;

                    const currentSheetIndex = Math.floor(top / TOTAL_CYCLE_PX);
                    const sheetStart = currentSheetIndex * TOTAL_CYCLE_PX;
                    const topInSheet = top - sheetStart;
                    
                    const spillsIntoNextSheet = (topInSheet + height) > THRESHOLD_PX;
                    const canFitOnOnePage = height <= THRESHOLD_PX;

                    if (spillsIntoNextSheet && canFitOnOnePage) {
                        const nextPageStart = (currentSheetIndex + 1) * TOTAL_CYCLE_PX;
                        const pushAmount = nextPageStart - top;
                        
                        if (pushAmount > 0) {
                            el.style.marginTop = pushAmount + "px";
                            
                            // ORPHAN PROTECTION: If we push this entry, also push the header if it was right before
                            // This prevents headers like "EDUCATION" from staying at the bottom of the previous page
                            if (i > 0) {
                                const prev = elements[i-1];
                                if (prev.tagName.match(/H[1-6]/i) || prev.classList.contains('section-header')) {
                                    prev.style.marginTop = (parseFloat(prev.style.marginTop) || 0) + pushAmount + "px";
                                }
                            }
                        }
                    }
                });
            }

            // Execute single-pass
            processSinglePass();
        }

        // Multiple triggers for stable rendering
        window.addEventListener('load', reconcilePageBreaks);
        window.addEventListener('resize', reconcilePageBreaks);
        setTimeout(reconcilePageBreaks, 300);
        setTimeout(reconcilePageBreaks, 2000); 
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
