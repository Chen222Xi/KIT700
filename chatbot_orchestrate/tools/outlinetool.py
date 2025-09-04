# outlinetool.py
# Minimal ADK tool so Orchestrate can import and register these functions.

import re
from typing import Dict, List
from ibm_watsonx_orchestrate.agent_builder.tools import tool  # correct path for ADK 1.9

SECTION_TITLES = [
    "Contact Details",
    "Unit Description",
    "Intended Learning Outcomes",
    "Requisites",
    "Alterations as a Result of Student Feedback",
    "Teaching Arrangements",
    "Assessment Schedule",
    "Assessment Details",
    "How your final result is determined",
    "Academic Progress Review",
    "Submission of assignments",
    "Academic integrity",
    "Requests for extensions",
    "Late penalties",
    "Review of results and appeals",
    "Required Resources",
    "Recommended Reading Materials",
    "Required reading materials",
    "Recommended reading materials",
    "Other required resources",
]

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

@tool(name="extract_section", description="Extract a target section summary and bullets from a UTAS unit outline text.")
def extract_section(text: str, target: str) -> Dict:
    """
    Args:
      text: raw outline text (a retrieved chunk or merged paragraphs)
      target: section title to extract (case-insensitive)
    Returns:
      dict with section, summary, bullets (JSON-serializable)
    """
    tnorm = target.lower().strip()
    choices = {t.lower(): t for t in SECTION_TITLES}
    if tnorm not in choices:
        for k in choices:
            if tnorm in k:
                tnorm = k
                break
    sec_name = choices.get(tnorm, target)

    # slice text between headings
    pat = r"(?mi)^(%s)\s*$" % "|".join([re.escape(t) for t in SECTION_TITLES])
    boundaries = [m for m in re.finditer(pat, text)]
    chunk = text
    for i, m in enumerate(boundaries):
        if m.group(1).lower() == sec_name.lower():
            start = m.end()
            end = boundaries[i + 1].start() if i + 1 < len(boundaries) else len(text)
            chunk = text[start:end]
            break

    body = _normalize(chunk)[:800]
    bullets: List[str] = []
    for p in re.split(r"(?<=[\.;])\s+|\n+", chunk):
        p = _normalize(p)
        if 6 <= len(p) <= 200:
            bullets.append(p)
        if len(bullets) >= 6:
            break

    return {"section": sec_name, "summary": body, "bullets": bullets}

@tool(name="extract_assessment_items", description="Extract assessment items and weight percentages from outline text.")
def extract_assessment_items(text: str) -> Dict:
    """
    Args:
      text: raw text containing assessment content
    Returns:
      dict with items [{name, weight}], and a note (JSON-serializable)
    """
    items: Dict[str, Dict] = {}
    # "Assessment Task n: Name"
    for m in re.finditer(r"(?mi)\b(?:Assessment\s*Task|Task)\s*\d+\s*:\s*([^\n%]{3,80})", text):
        name = _normalize(m.group(1))
        if name:
            items.setdefault(name, {"name": name, "weight": None})

    # common keywords
    name_keywords = [
        r"e[- ]?portfolio", r"literature review", r"qualitative methods",
        r"quantitative methods", r"online test", r"quiz", r"project\s*\d+",
        r"weekly tutorial tasks?"
    ]
    for kw in name_keywords:
        for m in re.finditer(kw, text, flags=re.I):
            pretty = re.sub(r"\s+", " ", m.group(0)).strip().title()
            items.setdefault(pretty, {"name": pretty, "weight": None})

    # attach nearest percentages
    percents = [(m.group(1), m.start()) for m in re.finditer(r"(?i)(\d{1,3})\s*%", text)]
    for name in list(items):
        pos = text.lower().find(name.lower())
        if pos >= 0 and percents:
            near = min(percents, key=lambda x: abs(x[1] - pos))
            items[name]["weight"] = f"{near[0]}%"

    # dedup by name
    seen, dedup = set(), []
    for it in items.values():
        key = it["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(it)

    return {"items": dedup, "note": "If items or weights are missing, context may be incomplete."}
