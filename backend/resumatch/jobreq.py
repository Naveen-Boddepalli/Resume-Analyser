"""Segment a job description into weighted requirement units.

Job postings mix requirements with company marketing, benefits and legal
boilerplate. Scoring against the whole text dilutes the signal, so each
sentence is classified as required / preferred / duty / other, and boilerplate
is dropped. Weights are fixed constants, not learned.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .text import normalize, split_sentences

KIND_WEIGHT = {"required": 1.0, "duty": 0.75, "preferred": 0.5, "other": 0.4}

_BOILERPLATE = re.compile(
    r"equal opportunity|equal employment|\beeo\b|affirmative action|without regard to|protected (?:veteran|characteristic)|"
    r"reasonable accommodation|vaccinat|covid|sponsorship|visa|401\(?k\)?|health insurance|dental|vision plan|"
    r"paid time off|\bpto\b|flexible spending|salary range|base pay|compensation package|total rewards|"
    r"we offer|benefits package|about (?:us|the company)|who we are|our (?:mission|values|culture)|"
    r"employees? (?:in|across)|clients in more than|global (?:leader|company|provider)|follow us|apply (?:now|today)|"
    r"background check|drug (?:test|screen)|relocation|travel (?:domestically|internationally)|"
    r"w-?2|c2c|corp[- ]to[- ]corp|immediate need|contract to hire|rate\b|per hour",
    re.I,
)
_REQUIRED_CUE = re.compile(
    r"\b(?:required|requirements?|must(?: have)?|minimum|mandatory|need(?:s|ed)? to|"
    r"proficien\w+|expert(?:ise)? in|strong (?:knowledge|background|experience|understanding)|"
    r"\d+\+?\s*(?:years|yrs)|degree in|bachelor|master)\b",
    re.I,
)
_PREFERRED_CUE = re.compile(
    r"\b(?:preferred|nice to have|a plus|is a plus|bonus|desired|ideally|advantageous|good to have)\b",
    re.I,
)
_HEADERS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(?:preferred|desired|nice[- ]to[- ]have|bonus)\s+(?:skills|qualifications|experience)?\s*:?|"
            r"nice to have\s*:?",
            re.I,
        ),
        "preferred",
    ),
    (
        re.compile(
            r"(?:key\s+)?(?:responsibilities|duties)\s*:|what you(?:'|’)?ll do\s*:?|"
            r"how you(?:'|’)?ll make a difference|role details\s*:?|job duties\s*:?",
            re.I,
        ),
        "duty",
    ),
    (
        re.compile(
            r"(?:minimum |basic |required |key )?(?:requirements|qualifications|skills)\s*:|"
            r"what you bring(?: to the table)?|must haves?\s*:?|you have\s*:|"
            r"required (?:skills|experience)\s*:?|experience(?: and skills)? required\s*:?",
            re.I,
        ),
        "required",
    ),
    (
        re.compile(
            r"(?:benefits|perks|compensation|about (?:us|the company|[A-Z]\w+)|who we are|"
            r"why (?:join|you want to work)|equal opportunity|our culture|company overview)\s*:?",
        ),
        "boilerplate",
    ),
]


@dataclass(frozen=True)
class Requirement:
    text: str
    kind: str
    weight: float


def _split_blocks(text: str) -> list[tuple[str, str]]:
    """Return ``[(kind, block_text)]`` by scanning for section headers."""
    hits: list[tuple[int, int, str]] = []
    for pattern, kind in _HEADERS:
        for m in pattern.finditer(text):
            hits.append((m.start(), m.end(), kind))
    hits.sort()
    # Drop overlapping header matches, keep earliest.
    merged: list[tuple[int, int, str]] = []
    for s, e, k in hits:
        if merged and s < merged[-1][1]:
            continue
        merged.append((s, e, k))
    if not merged:
        return [("other", text)]
    blocks = [("other", text[: merged[0][0]])]
    for i, (_, e, k) in enumerate(merged):
        nxt = merged[i + 1][0] if i + 1 < len(merged) else len(text)
        blocks.append((k, text[e:nxt]))
    return blocks


def parse_requirements(jd_text: str, min_words: int = 4) -> list[Requirement]:
    """Classify the sentences of a JD, dropping boilerplate."""
    out: list[Requirement] = []
    for block_kind, block in _split_blocks(normalize(jd_text)):
        if block_kind == "boilerplate":
            continue
        for sent in split_sentences(block, min_words=min_words, max_words=45):
            if _BOILERPLATE.search(sent):
                continue
            kind = block_kind
            if _PREFERRED_CUE.search(sent):
                kind = "preferred"
            elif kind in ("other", "duty") and _REQUIRED_CUE.search(sent):
                kind = "required" if kind == "other" else "duty"
            out.append(Requirement(sent, kind, KIND_WEIGHT[kind]))
    if not out:  # degenerate JD: fall back to every sentence
        out = [Requirement(s, "other", KIND_WEIGHT["other"]) for s in split_sentences(normalize(jd_text))]
    return out
