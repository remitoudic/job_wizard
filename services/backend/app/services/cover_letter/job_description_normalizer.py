import re
import json
from typing import Dict, List


# ----------------------------
# Noise & footer filtering
# ----------------------------

NOISE_PATTERNS = [
    r"show more",
    r"show less",
    r"equal[- ]opportunity",
    r"privacy policy",
    r"covey",
    r"data protection",
    r"recruitment",
    r"nyc local law",
    r"@",
]


# ----------------------------
# Semantic section detection
# ----------------------------

SECTION_HINTS = {
    "Company": ["about", "who we are", "we offer", "our platform"],
    "Role": ["about the role", "the role"],
    "Responsibilities": ["responsibilities", "in this role", "you will"],
    "Requirements": ["requirements", "you are", "bachelor", "years of experience"],
    "Compensation": ["compensation", "usd", "salary", "per hour", "pay"],
    "Location": ["location", "remote", "fully remote"],
    "Contract": ["contract", "project-based"],
    "Benefits": ["benefits", "rewards", "perks"],
}


TECH_PATTERN = re.compile(
    r"\b(Python|JavaScript|TypeScript|Go|C\+\+|Ruby|Postgres|React|Docker|Kubernetes|AWS|REST|GraphQL)\b",
    re.I,
)

MONEY_PATTERN = re.compile(
    r"\$?\d+(?:\.\d+)?\s?(?:USD|EUR|GBP)?(?:\s?per\s?hour)?", re.I
)


# ----------------------------
# Normalization
# ----------------------------


def normalize(text: str) -> str:
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def is_noise(line: str) -> bool:
    return any(re.search(p, line.lower()) for p in NOISE_PATTERNS)


def detect_section(line: str) -> str | None:
    line_lower = line.lower()
    for section, hints in SECTION_HINTS.items():
        if any(h in line_lower for h in hints):
            return section
    return None


# ----------------------------
# Sectioning
# ----------------------------


def split_sections(text: str) -> Dict[str, List[str]]:
    sections = {"Overview": []}
    current = "Overview"

    for line in text.split("\n"):
        line = line.strip()
        if not line or is_noise(line):
            continue

        new = detect_section(line)
        if new:
            current = new
            sections.setdefault(current, [])
            continue

        sections.setdefault(current, []).append(line)

    return sections


# ----------------------------
# Bullet normalization
# ----------------------------


def to_bullets(lines: List[str]) -> List[str]:
    bullets = []
    for line in lines:
        parts = re.split(r"\. |\; ", line)
        bullets.extend(p.strip() for p in parts if len(p.strip()) > 10)
    return bullets


# ----------------------------
# Metadata extraction
# ----------------------------


def extract_metadata(text: str) -> Dict[str, str]:
    money = MONEY_PATTERN.findall(text)
    tech = sorted(set(m.group(0) for m in TECH_PATTERN.finditer(text)))

    contract = "contract" if "contract" in text.lower() else "full-time"
    remote = "remote" if "remote" in text.lower() else "on-site"

    return {
        "compensation": money[0] if money else None,
        "contract_type": contract,
        "work_mode": remote,
        "tech_stack": tech,
    }


# ----------------------------
# Markdown rendering
# ----------------------------


def render_markdown(sections: Dict[str, List[str]], meta: Dict[str, str]) -> str:
    md = []

    for title, lines in sections.items():
        if not lines:
            continue

        md.append(f"## {title}")
        for b in to_bullets(lines):
            md.append(f"- {b}")
        md.append("")

    md.append("## Metadata")
    for k, v in meta.items():
        md.append(f"- {k}: {v}")

    return "\n".join(md)


# ----------------------------
# JSON rendering
# ----------------------------


def render_json(sections: Dict[str, List[str]], meta: Dict[str, str]) -> Dict:
    return {
        "sections": {
            title: to_bullets(lines) for title, lines in sections.items() if lines
        },
        "metadata": meta,
    }


# ----------------------------
# Public API
# ----------------------------


def normalize_job_post(raw: str) -> Dict[str, str]:
    clean = normalize(raw)
    sections = split_sections(clean)
    meta = extract_metadata(raw)

    return {
        "markdown": render_markdown(sections, meta),
        "json": json.dumps(render_json(sections, meta), indent=2),
    }
