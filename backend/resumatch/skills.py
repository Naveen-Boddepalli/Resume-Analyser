"""Transparent skill lexicon: alias normalisation, matching and induction."""

from __future__ import annotations

import re
from collections import Counter
from importlib import resources
from typing import Iterable

from .text import STOPWORDS, tokenize

# Aliases that are ordinary English words are only accepted in this exact casing.
_CASE_SENSITIVE = {"excel": "Excel", "swift": "Swift", "lean": "Lean", "rust": "Rust"}
_SKILL_HEADER = re.compile(
    r"(?:Technical Skills|Core Qualifications|Skill Highlights|Skills|Key Skills|"
    r"Areas of Expertise|Core Competencies)(?![a-z])"
)
_SECTION_END = re.compile(
    r"(?:Professional Experience|Work (?:History|Experience)|Experience|Education|"
    r"Certifications?|Accomplishments|Summary|Professional Summary|Additional Information|"
    r"Work Experience|Employment History|Projects?)(?![a-z])"
)
_MAX_NGRAM = 4


class SkillLexicon:
    """Maps surface forms to canonical skill names.

    The lexicon is a plain dictionary from token tuples to canonical names; a
    match is the longest alias starting at a token position.
    """

    def __init__(self, entries: dict[str, list[str]]):
        self.entries = entries
        self._index: dict[tuple[str, ...], str] = {}
        for canon, aliases in entries.items():
            for form in [canon, *aliases]:
                toks = tuple(tokenize(form))
                if toks and len(toks) <= _MAX_NGRAM:
                    self._index.setdefault(toks, canon)

    @classmethod
    def from_seed(cls, extra: Iterable[str] = ()) -> "SkillLexicon":
        text = (resources.files("resumatch") / "data" / "skills_seed.txt").read_text("utf-8")
        entries: dict[str, list[str]] = {}
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            canon, _, rest = line.partition(":")
            entries[canon.strip().lower()] = [a.strip() for a in rest.split(";") if a.strip()]
        for phrase in extra:
            entries.setdefault(phrase.strip().lower(), [])
        return cls(entries)

    def __len__(self) -> int:
        return len(self.entries)

    def __contains__(self, canon: str) -> bool:
        return canon in self.entries

    def find(self, text: str) -> list[str]:
        """Canonical skills mentioned in ``text`` (in order, with repeats)."""
        toks = tokenize(text)
        original = re.findall(r"\.?[A-Za-z0-9]+(?:[.+#/&'-][A-Za-z0-9]+)*[+#]*", text)
        found: list[str] = []
        i = 0
        while i < len(toks):
            hit = None
            for n in range(min(_MAX_NGRAM, len(toks) - i), 0, -1):
                canon = self._index.get(tuple(toks[i : i + n]))
                if canon is not None:
                    if n == 1 and toks[i] in _CASE_SENSITIVE:
                        surface = original[i] if i < len(original) else toks[i]
                        if surface not in (_CASE_SENSITIVE[toks[i]], _CASE_SENSITIVE[toks[i]].upper()):
                            continue
                    hit = (canon, n)
                    break
            if hit:
                found.append(hit[0])
                i += hit[1]
            else:
                i += 1
        return found

    def find_by_sentence(self, sentences: list[str]) -> dict[str, list[int]]:
        """Skill -> indices of the sentences that mention it (evidence trail)."""
        out: dict[str, list[int]] = {}
        for idx, sent in enumerate(sentences):
            for canon in dict.fromkeys(self.find(sent)):
                out.setdefault(canon, []).append(idx)
        return out


def skills_section(text: str, max_chars: int = 700) -> str:
    """Best-effort extraction of the skills block of a resume."""
    m = _SKILL_HEADER.search(text)
    if not m:
        return ""
    tail = text[m.end() : m.end() + max_chars]
    end = _SECTION_END.search(tail)
    return tail[: end.start()] if end else tail


def induce_vocabulary(
    resume_texts: Iterable[str],
    lexicon: SkillLexicon,
    min_df: int = 8,
    max_tokens: int = 3,
) -> list[str]:
    """Mine frequent comma-separated items from resume skills sections.

    Must be called with **training resumes only** so that no test text leaks
    into the vocabulary. Items already covered by the seed lexicon, stop-word
    only items and items containing digits-only or tiny tokens are skipped.
    """
    df: Counter[str] = Counter()
    for text in resume_texts:
        block = skills_section(text)
        items = {" ".join(tokenize(part)) for part in re.split(r"[,;|•\n]+", block) if 2 < len(part.strip()) <= 32}
        df.update(i for i in items if i)
    vocab = []
    for item, count in df.items():
        toks = item.split()
        if count < min_df or len(toks) > max_tokens:
            continue
        if all(t in STOPWORDS or t.isdigit() or len(t) < 2 for t in toks):
            continue
        if tuple(toks) in lexicon._index:
            continue
        vocab.append(item)
    return sorted(vocab)
