# CV PDF Creation Logic (WeasyPrint)

This document explains the technical implementation of the PDF generation logic for CVs, ensuring visual consistency and professional formatting.

## Core Implementation
The PDF generation logic is primarily handled in:
- **Service:** `cv_generator_service.py` (specifically the `generate_pdf` method).
- **Styles:** Template-specific CSS files (e.g., `modern.css`) located in the `cv_templates` directory.

## Key Principles

### 1. Standardized Geometry
The system uses the CSS `@page` rule to establish a strict physical layout:
- **Size:** A4 (210mm x 297mm).
- **Margins:** 1.5cm on all sides.
- **Goal:** Ensures the document prints perfectly on standard paper without content cut-off.

### 2. Atomic Blocks (Fragment Prevention)
To prevent awkward page breaks where a job description or education entry is split across two pages, we use:
- **CSS Rule:** `page-break-inside: avoid;`
- **Targets:** Applied to specific classes like `.experience-item` and `.education-item`.
- **Effect:** If an entry doesn't fit at the bottom of a page, the entire block is moved to the top of the next page.

### 3. Float-Based Layout
While modern web design favors Flexbox and Grid, WeasyPrint handles pagination and multi-column wrapping more reliably using traditional floats:
- **Mechanism:** Uses `float: left` and `float: right` for the sidebar/main content split.
- **Rationale:** This prevents columns from "breaking" inconsistently when content spills over to multiple pages.

### 4. Implicit Flow & Rendering
The rendering engine follows standard CSS Paged Media standards:
- **Natural Pagination:** Content flows vertically; as it reaches the 297mm limit (adjusted for margins), a new page is automatically instantiated.
- **Base URL Mapping:** Asset paths (images, fonts) are resolved relative to the `cv_templates` directory to ensure WeasyPrint can fetch them during the build.

)
---

## Browser Preview Reconciliation Logic (v2.0)

Because browsers (Chrome/WebKit/Firefox) render typography and spacing differently than PDF engines like WeasyPrint, a separate **JavaScript Reconciliation Layer** ensures visual parity.

### 1. The Cycle Math
The browser preview uses a "Cascading Sheet" simulation where each sheet repeats every **299mm** (297mm A4 + 2mm Gap). The JavaScript logic must remain perfectly synchronized with this cycle:
- **`TOTAL_CYCLE_PX = 299mm * pxPerMm`**
- **Trigger Threshold:** Pushing an element happens at a safe "threshold" (currently **97.0%** of the page height) to ensure Chrome's taller rendering doesn't cause text to overlap the gap.

### 2. Internal Calibration (New in v2.0)
To account for browser `zoom` and scaling inaccuracies, the script now places a **100mm test ruler INSIDE** the scaled CV container. This ensures that the `pxPerMm` ratio is measured at the same scale as the actual content, eliminating coordinate drift.

### 3. Column-Aware Processing
The algorithm now recognizes multi-column layouts (floats):
- **Grouping:** Elements are grouped into columns based on their horizontal `left` coordinates.
- **Independent Flow:** Pushing an element in the Sidebar does not affect the Main Content's vertical flow, and vice-versa.

### 4. Atomic Blocks & Orphan Protection
- **Selectors:** `.experience-item`, `.education-item`, `section.section`.
- **Orphan Protection:** If a block is pushed to the next page, the script checks if the preceding element was a header (e.g., `H2` or `.section-header`). If so, the header is pushed along with its first child to prevent "lonely headers" at the bottom of pages.

### 5. Calibration Factor
- **Safety Margin (0.970):** Provides an ~8mm "cushion" at the bottom of each page. This accounts for minor layout variations and prevents text from being sliced by the page-break visualization.

---
> [!NOTE]
> This logic is designed specifically for **WeasyPrint**. Browser-based previews use a separate JavaScript-based "Reconciliation Logic" to mimic these behaviors.
