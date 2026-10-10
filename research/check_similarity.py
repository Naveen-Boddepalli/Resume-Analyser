"""Self-check: word n-gram overlap between the manuscript and the abstracts it cites.

This is *not* a substitute for a publisher's similarity service (iThenticate,
Turnitin) and says nothing about AI-text detectors, which are unreliable. It
only answers one narrow question: did we reuse phrasing from the abstracts of
the works we cite? Abstracts are fetched from the arXiv API at run time.

    .venv/bin/python -I research/check_similarity.py
"""

from __future__ import annotations

import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script dir

from common import ROOT

N = 5  # word n-gram length
ATOM = {"a": "http://www.w3.org/2005/Atom"}


def arxiv_ids() -> list[str]:
    bib = (ROOT / "paper" / "references.bib").read_text()
    return sorted(set(re.findall(r"eprint = \{arXiv:(\d{4}\.\d{4,5})\}", bib)))


def fetch_abstracts(ids: list[str]) -> dict[str, str]:
    url = "https://export.arxiv.org/api/query?id_list=" + ",".join(ids) + f"&max_results={len(ids)}"
    data = b""
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:  # nosec B310 - fixed https host
                data = r.read()
            break
        except Exception:  # noqa: BLE001 - arXiv rate-limits bursts; back off and retry
            time.sleep(5 * 2**attempt)
    root = ET.fromstring(data)  # nosec B314 - response from a fixed https arXiv endpoint, no entity expansion needed
    out = {}
    for e in root.findall("a:entry", ATOM):
        aid = e.find("a:id", ATOM).text.split("/abs/")[-1].split("v")[0]  # type: ignore[union-attr]
        out[aid] = " ".join(e.find("a:summary", ATOM).text.split())  # type: ignore[union-attr]
    return out


def strip_tex(text: str) -> str:
    text = re.sub(r"(?<!\\)%.*", "", text)
    text = re.sub(
        r"\\begin\{(equation|align|tabular|table\*?|figure\*?|tikzpicture)\}.*?\\end\{\1\}", " ", text, flags=re.S
    )
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(r"\\(cite|ref|label|input|includegraphics)(\[[^\]]*\])?\{[^}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}~\\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def ngrams(tokens: list[str], n: int = N) -> set[tuple[str, ...]]:
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def main() -> None:
    ids = arxiv_ids()
    abstracts = fetch_abstracts(ids)
    time.sleep(1)
    sections = sorted((ROOT / "paper" / "sections").glob("*.tex"))
    missing = sorted(set(ids) - set(abstracts))
    print(
        f"{len(abstracts)}/{len(ids)} abstracts of cited arXiv works fetched"
        + (f" (missing: {missing})" if missing else "")
    )
    print(f"{N}-gram overlap per section\n")
    worst = 0.0
    all_tokens: list[str] = []
    for path in sections:
        toks = words(strip_tex(path.read_text()))
        all_tokens += toks
        grams = ngrams(toks)
        if not grams:
            continue
        hits = {aid: len(grams & ngrams(words(a))) for aid, a in abstracts.items()}
        total = len(set().union(*(grams & ngrams(words(a)) for a in abstracts.values())))
        top = max(hits, key=lambda k: hits[k])
        share = total / len(grams)
        worst = max(worst, share)
        print(
            f"{path.name:22s} words={len(toks):5d}  shared {N}-grams={total:3d} ({share:5.1%})  max single source: {top} ({hits[top]})"
        )
    print(f"\nmanuscript words (prose, math/tables/figures removed): {len(all_tokens)}")
    print(f"highest per-section share of {N}-grams that also occur in a cited abstract: {worst:.1%}")


if __name__ == "__main__":
    main()
