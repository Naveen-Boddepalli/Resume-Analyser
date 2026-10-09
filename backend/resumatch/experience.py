"""Years-of-experience and education-level extraction (rule based)."""

from __future__ import annotations

import re
from datetime import date

_YEARS_STMT = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b", re.I)
_DATE = r"(?:(\d{1,2})/)?((?:19|20)\d{2})"
_RANGE = re.compile(
    rf"{_DATE}\s*(?:to|-|–|until)\s*(?:{_DATE}|(present|current|now|till date))",
    re.I,
)

_EDU_PATTERNS: list[tuple[int, re.Pattern[str]]] = [
    (4, re.compile(r"\b(?:ph\.?\s?d|doctorate|doctoral|d\.phil)\b", re.I)),
    (
        3,
        re.compile(
            r"\b(?:master'?s?|m\.?\s?sc?\.?|m\.?\s?tech|m\.?\s?eng|mba|m\.?\s?a\.?|m\.?\s?s\.? in)\b",
            re.I,
        ),
    ),
    (
        2,
        re.compile(
            r"\b(?:bachelor'?s?|b\.?\s?sc?\.?|b\.?\s?tech|b\.?\s?e\.|b\.?\s?a\.? in|undergraduate degree|b\.?\s?com)\b",
            re.I,
        ),
    ),
    (1, re.compile(r"\b(?:associate'?s?(?: degree)?|diploma|certificate program)\b", re.I)),
]


def required_years(jd_text: str) -> float:
    """Largest ``N years`` figure in a JD, ignoring implausible values."""
    vals = [int(m.group(1)) for m in _YEARS_STMT.finditer(jd_text) if 0 < int(m.group(1)) <= 25]
    return float(max(vals)) if vals else 0.0


def resume_years(text: str, today: date | None = None) -> float:
    """Estimate total professional experience in years.

    Takes the maximum of (a) the largest explicit ``N years`` statement near the
    word *experience* and (b) the union of dated ranges such as
    ``05/2017 to Present``.
    """
    today = today or date.today()
    explicit = 0.0
    for m in _YEARS_STMT.finditer(text):
        window = text[max(0, m.start() - 60) : m.end() + 60].lower()
        if "experience" in window and 0 < int(m.group(1)) <= 45:
            explicit = max(explicit, float(m.group(1)))

    spans: list[tuple[int, int]] = []
    for m in _RANGE.finditer(text):
        s_month = int(m.group(1)) if m.group(1) else 1
        s_year = int(m.group(2))
        if m.group(5):
            e_year, e_month = today.year, today.month
        else:
            e_year = int(m.group(4))
            e_month = int(m.group(3)) if m.group(3) else 12
        s = s_year * 12 + max(1, min(12, s_month))
        e = e_year * 12 + max(1, min(12, e_month))
        if 0 < e - s <= 12 * 45 and s_year >= 1960 and e_year <= today.year + 1:
            spans.append((s, e))
    spans.sort()
    total, cur_s, cur_e = 0, None, None
    for s, e in spans:
        if cur_e is None or s > cur_e:
            if cur_s is not None and cur_e is not None:
                total += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_s is not None and cur_e is not None:
        total += cur_e - cur_s
    return float(min(45.0, max(explicit, total / 12.0)))


def education_level(text: str) -> int:
    """Highest education level mentioned: 0 none, 1 diploma, 2 bachelor, 3 master, 4 doctorate."""
    for level, pat in _EDU_PATTERNS:
        if pat.search(text):
            return level
    return 0


def required_education(jd_text: str) -> int:
    """Minimum education level a JD asks for (lowest level among those mentioned)."""
    levels = [lvl for lvl, pat in _EDU_PATTERNS if pat.search(jd_text)]
    return min(levels) if levels else 0
