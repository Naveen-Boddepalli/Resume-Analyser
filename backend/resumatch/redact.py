"""Blind-screening front end: remove identity cues before any scoring.

The redactor is rule based on purpose: it is deterministic, auditable and
needs no model download. It removes *explicit* identifiers (names in the
header, contact details, personal-detail fields, honorifics, gendered
pronouns, institution names, graduation dates). Proxy signals that survive
redaction are measured, not assumed away; see ``resumatch.fairness``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_URL = re.compile(
    r"(?:https?://|www\.)\S+|(?:linkedin|github|gitlab|twitter|facebook|instagram)\.com/\S*",
    re.I,
)
_PHONE = re.compile(r"(?<![\w/])\+?\(?\d[\d\s().-]{8,18}\d(?![\w/])")
_PERSONAL_FIELD = re.compile(
    r"\b(?:date of birth|d\.?o\.?b\.?|marital status|gender|sex|nationality|religion|caste|"
    r"father'?s name|mother'?s name|spouse|age|passport(?: no\.?| number)?|visa status)\b"
    r"\s*[:\-]\s*[^,;|\n]{1,40}",
    re.I,
)
_HONORIFIC = re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Mx|Dr|Shri|Smt|Sri)\.?(?=\s+[A-Z])")
_NAME_LABEL = re.compile(r"\b(?:Full\s+)?Name\s*[:\-]\s*([A-Z][\w'.-]+(?:\s+[A-Z][\w'.-]+){0,3})")
_HEADER_NAME = re.compile(r"^\s*([A-Z][\w'.-]+(?:[ \t]+[A-Z][\w'.-]+){1,3})[ \t]*(?:\n|$|[|,\u2022])")
_NOT_NAME = frozenset(
    "resume curriculum vitae cv summary profile objective experience education skills "
    "contact professional career personal details".split()
)
_INSTITUTION = re.compile(
    r"\b(?:(?:The\s+)?(?:[A-Z][\w&'.-]*\s+){0,4}"
    r"(?:University|College|Institute of Technology|Institute|Polytechnic|Academy|School of [A-Z]\w+)"
    r"(?:\s+of\s+(?:[A-Z][\w&'.-]*\s*){1,3})?)"
)
_UNIV_OF = re.compile(r"\bUniversity of (?:[A-Z][\w&'.-]*\s*){1,3}")
_GRAD_DATE = re.compile(
    r"\b(?:expected\s+in|graduat(?:ed|ion)(?:\s+date)?|class\s+of)\s*:?\s*(?:\d{1,2}/)?(?:19|20)\d{2}",
    re.I,
)

_PRONOUNS = {
    "he": "they",
    "she": "they",
    "him": "them",
    "her": "their",
    "his": "their",
    "hers": "theirs",
    "himself": "themselves",
    "herself": "themselves",
}
_PRONOUN_RE = re.compile(r"\b(" + "|".join(_PRONOUNS) + r")\b", re.I)
_GENDERED_TERMS = {
    "chairman": "chairperson",
    "chairwoman": "chairperson",
    "salesman": "salesperson",
    "saleswoman": "salesperson",
    "businessman": "businessperson",
    "businesswoman": "businessperson",
    "waitress": "server",
    "waiter": "server",
    "actress": "actor",
    "stewardess": "flight attendant",
    "policeman": "police officer",
    "fireman": "firefighter",
    "foreman": "supervisor",
}
_GENDERED_RE = re.compile(r"\b(" + "|".join(_GENDERED_TERMS) + r")\b", re.I)
# Gender-marked organisation names are removed as a *named* proxy class so that
# the audit can state exactly which proxies the redactor does and does not handle.
_GENDERED_ORG = re.compile(
    r"\b(?:Society of Women Engineers|Women in (?:Tech|Technology|Engineering|Science)|"
    r"Women'?s\s+(?:\w+\s+){0,2}(?:Club|Society|Association|Team|Network)|"
    r"Girls'?\s+(?:\w+\s+){0,2}(?:Club|Team)|Sorority|Fraternity|"
    r"Men'?s\s+(?:\w+\s+){0,2}(?:Club|Society|Association|Team|Network))\b",
    re.I,
)


@dataclass
class RedactionReport:
    """How many items of each class were removed (never the removed text)."""

    counts: dict[str, int] = field(default_factory=dict)

    def add(self, kind: str, n: int = 1) -> None:
        if n:
            self.counts[kind] = self.counts.get(kind, 0) + n

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def _looks_like_name(candidate: str) -> bool:
    """Reject section headers and job titles (including headers glued to the next word)."""
    for tok in candidate.split():
        low = tok.lower().strip(".,'-")
        if low in _NOT_NAME or low.startswith(tuple(_NOT_NAME)) or len(tok) > 18:
            return False
        if sum(c.isupper() for c in tok) > 2 or any(c.isdigit() for c in tok):
            return False
    return True


def _sub_count(pattern: re.Pattern[str], repl: str, text: str, kind: str, rep: RedactionReport) -> str:
    text, n = pattern.subn(repl, text)
    rep.add(kind, n)
    return text


def _phone_repl(m: re.Match[str], rep: "RedactionReport") -> str:
    digits = sum(c.isdigit() for c in m.group(0))
    if 9 <= digits <= 13 and not re.fullmatch(r"(?:\s*(?:19|20)\d{2}\s*)+", m.group(0)):
        rep.add("phone")
        return "[PHONE]"
    return m.group(0)


def _match_case(src: str, repl: str) -> str:
    return repl.capitalize() if src[:1].isupper() else repl


def redact(
    text: str,
    *,
    known_names: list[str] | None = None,
    institutions: bool = True,
    gendered_orgs: bool = True,
) -> tuple[str, RedactionReport]:
    """Return ``(redacted_text, report)``.

    ``known_names`` lets a caller supply names it already knows (for example
    from an application form) so they are removed wherever they occur.
    """
    rep = RedactionReport()

    # Header name: first line that looks like a person name.
    m = _HEADER_NAME.match(text)
    if m and _looks_like_name(m.group(1)):
        text = "[NAME]" + text[m.end(1) :]
        rep.add("name")
    text, n = _NAME_LABEL.subn("Name: [NAME]", text)
    rep.add("name", n)
    for name in known_names or []:
        if name.strip():
            text, n = re.subn(re.escape(name.strip()), "[NAME]", text, flags=re.I)
            rep.add("name", n)

    text = _sub_count(_EMAIL, "[EMAIL]", text, "email", rep)
    text = _sub_count(_URL, "[URL]", text, "url", rep)
    text = _PHONE.sub(lambda m: _phone_repl(m, rep), text)
    text = _sub_count(_PERSONAL_FIELD, "[PERSONAL]", text, "personal_field", rep)
    text = _sub_count(_HONORIFIC, "", text, "honorific", rep)
    text = _sub_count(_GRAD_DATE, "[DATE]", text, "graduation_date", rep)
    if institutions:
        text = _sub_count(_UNIV_OF, "[INSTITUTION]", text, "institution", rep)
        text = _sub_count(_INSTITUTION, "[INSTITUTION]", text, "institution", rep)
    if gendered_orgs:
        text = _sub_count(_GENDERED_ORG, "[ORGANISATION]", text, "gendered_org", rep)

    def _pron(mt: re.Match[str]) -> str:
        return _match_case(mt.group(0), _PRONOUNS[mt.group(0).lower()])

    def _term(mt: re.Match[str]) -> str:
        return _match_case(mt.group(0), _GENDERED_TERMS[mt.group(0).lower()])

    text, n = _PRONOUN_RE.subn(_pron, text)
    rep.add("pronoun", n)
    text, n = _GENDERED_RE.subn(_term, text)
    rep.add("gendered_term", n)
    return text, rep
