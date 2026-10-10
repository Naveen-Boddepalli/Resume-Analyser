"""Optional LLM narrative, constrained to the evidence the scorer produced.

The fit score, decision and every piece of evidence come from the deterministic
EviMatch pipeline. The LLM may only rephrase them; if the call fails, the caller
keeps the deterministic summary. The model never sees names or contact details
because it receives the analysis, which is built from redacted text.
"""

from __future__ import annotations

import json
from typing import Any

import requests

from config import ENABLE_LLM_NARRATIVE, MISTRAL_API_KEY, MISTRAL_API_URL, MISTRAL_MODEL

_INSTRUCTIONS = (
    "You write a 3-sentence note for a recruiter. Use ONLY the facts in the JSON. "
    "Do not infer the candidate's gender, age, ethnicity, nationality or background. "
    "Do not recommend hiring or rejecting; describe the evidence."
)


def llm_narrative(analysis: dict[str, Any], timeout: float = 15.0) -> str | None:
    if not (ENABLE_LLM_NARRATIVE and MISTRAL_API_KEY):
        return None
    facts = {
        "fit_score": analysis["fit_score"],
        "requirement_counts": analysis["requirement_counts"],
        "matching_skills": [m["skill"] for m in analysis["matching_skills"]][:10],
        "missing_skills": analysis["missing_skills"][:8],
        "experience": analysis["experience"],
    }
    payload: dict[str, Any] = {
        "model": MISTRAL_MODEL,
        "temperature": 0,
        "max_tokens": 160,
        "messages": [
            {"role": "system", "content": _INSTRUCTIONS},
            {"role": "user", "content": json.dumps(facts)},
        ],
    }
    try:
        r = requests.post(
            MISTRAL_API_URL, json=payload, headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"}, timeout=timeout
        )
        r.raise_for_status()
        return str(r.json()["choices"][0]["message"]["content"]).strip()
    except Exception:  # noqa: BLE001 - narrative is optional; callers keep the deterministic summary
        return None
