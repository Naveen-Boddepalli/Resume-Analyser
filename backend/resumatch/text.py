"""Text normalisation, sentence splitting and tokenisation helpers."""

from __future__ import annotations

import re
import unicodedata

_DASHES = {ord(c): "-" for c in "‐‑‒–—―"}
_GLUED_BOUNDARY = re.compile(r"([a-z0-9\)])([.;])(?=[A-Z][a-z])")
_NET_PREFIXES = ("asp", "vb", "c", "f")
_SENT_BOUNDARY = re.compile(r"(?<=[.!?;:])\s+(?=[A-Z0-9•\-\*\(])|\n+|•|\s\|\s|\s-\s(?=[A-Z])")
_TOKEN = re.compile(r"\.?[a-z0-9]+(?:[.+#/&'-][a-z0-9]+)*[+#]*")


def normalize(text: str) -> str:
    """Unicode-normalise, repair glued sentence boundaries and collapse spaces.

    Resumes extracted from PDF/DOCX (and the public benchmark used here) often
    contain run-together text such as ``"projects.Proven ability"``. Only the
    boundary between a lowercase character/digit, a full stop and a capitalised
    word is repaired; identifiers such as ``ASP.Net`` are left alone.
    """
    text = unicodedata.normalize("NFKC", text).translate(_DASHES)
    text = text.replace(" ", " ").replace("\r", "\n")

    def _fix(match: re.Match[str]) -> str:
        head = text[max(0, match.start() - 4) : match.start() + 1].lower()
        if match.group(2) == "." and head.rstrip(".").endswith(_NET_PREFIXES):
            return match.group(0)
        return f"{match.group(1)}{match.group(2)} "

    text = _GLUED_BOUNDARY.sub(_fix, text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def split_sentences(text: str, min_words: int = 3, max_words: int = 45) -> list[str]:
    """Split into sentence-like units, windowing very long run-on units."""
    units: list[str] = []
    for raw in _SENT_BOUNDARY.split(text):
        raw = raw.strip(" \t-*")
        if not raw:
            continue
        words = raw.split()
        if len(words) < min_words:
            continue
        for start in range(0, len(words), max_words):
            window = words[start : start + max_words]
            if len(window) >= min_words:
                units.append(" ".join(window))
    return units


def tokenize(text: str) -> list[str]:
    """Lower-case tokens that keep ``c++``, ``c#``, ``.net``, ``node.js``, ``ci/cd``."""
    return _TOKEN.findall(text.lower())


STOPWORDS = frozenset(
    "a an the and or of to in for on with at by from as is are be been being this that these those it its "
    "we you our your their they them he she his her i will can may must should would could shall not no "
    "than then so such into over under about across per via within without including include etc also "
    "have has had do does did using use used work works working able ability".split()
)
