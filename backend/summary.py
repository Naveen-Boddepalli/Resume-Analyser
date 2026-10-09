"""Deterministic plain-language summary built only from the evidence the model used."""

from __future__ import annotations

from typing import Any

_BAND = {
    "Shortlist": "The profile matches the posting well enough to shortlist.",
    "Review": "The profile partially matches the posting and needs human review.",
    "Reject": "The profile shows little overlap with the posting.",
}


def build_summary(analysis: dict[str, Any]) -> str:
    c = analysis["requirement_counts"]
    total = sum(c.values()) or 1
    parts = [
        f"Fit score {analysis['fit_score']:.0f}/100. {_BAND[analysis['decision']]}",
        f"{c['met']} of {total} job requirements are clearly evidenced in the resume, "
        f"{c['partial']} partially and {c['unmet']} not at all.",
    ]
    skills = [m["skill"] for m in analysis["matching_skills"]][:6]
    if skills:
        parts.append("Matched skills: " + ", ".join(skills) + ".")
    missing = analysis["missing_skills"][:5]
    if missing:
        parts.append("Required skills with no evidence: " + ", ".join(missing) + ".")
    exp = analysis["experience"]
    if exp["required_years"]:
        verdict = "meets" if exp["meets"] else "falls short of"
        parts.append(
            f"Estimated experience of {exp['candidate_years']:.0f} years {verdict} the stated "
            f"{exp['required_years']:.0f}-year requirement."
        )
    parts.append("This is decision support, not a decision: a person should review the evidence before any outcome.")
    return " ".join(parts)
