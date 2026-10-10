"""Counterfactual bias audit: perturb a resume, re-score, compare.

Design follows the audit-study tradition (Bertrand & Mullainathan 2004;
Wilson & Caliskan 2024): hold the content constant, change only a signal that
should be irrelevant, and measure how the score moves. Name lists are small,
fixed and stated here so the audit is reproducible; name-to-group association is
statistical and imperfect, which the paper states as a limitation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

# Four first-name/surname pairs per demographic cell (race/ethnicity x gender).
NAMES: dict[str, list[str]] = {
    "white_female": ["Emily Walsh", "Sarah Miller", "Megan Cooper", "Laurie Anderson"],
    "white_male": ["Greg Baker", "Matthew Clark", "Brad Thompson", "Todd Wilson"],
    "black_female": ["Lakisha Washington", "Tamika Jefferson", "Latoya Jackson", "Aisha Robinson"],
    "black_male": ["Jamal Jackson", "Darnell Williams", "Tyrone Freeman", "Kareem Johnson"],
    "hispanic_female": ["Maria Garcia", "Guadalupe Hernandez", "Carmen Rodriguez", "Ana Martinez"],
    "hispanic_male": ["Jose Hernandez", "Luis Gonzalez", "Carlos Ramirez", "Miguel Lopez"],
    "east_asian_female": ["Mei Chen", "Ling Zhang", "Yuna Kim", "Hui Wang"],
    "east_asian_male": ["Wei Zhang", "Jun Li", "Minjun Park", "Hao Liu"],
    "south_asian_female": ["Priya Sharma", "Ananya Iyer", "Lakshmi Reddy", "Sneha Patel"],
    "south_asian_male": ["Rahul Verma", "Arjun Nair", "Vikram Singh", "Amit Kumar"],
}

# Proxy cues. Each is compared with a neutral, similar-length control line.
PROXIES: dict[str, dict[str, str]] = {
    "affinity_org": {
        "control": "Member, Society of Professional Engineers",
        "black": "Member, National Society of Black Engineers",
        "hispanic": "Member, Society of Hispanic Professional Engineers",
        "east_asian": "Member, Asian American Engineers Association",
    },
    "hobbies": {
        "control": "Interests: reading, travel, photography, cooking",
        "female_coded": "Interests: yoga, knitting, baking, gardening",
        "male_coded": "Interests: football, weightlifting, fishing, motorcycles",
    },
    "career_break": {
        "control": "Career break (2019-2021): full-time study",
        "childcare": "Career break (2019-2021): full-time childcare",
    },
    # Named proxy the redactor is designed to remove. The control is the opposite gender marker,
    # so with redaction on both lines become the same placeholder and the comparison does not
    # measure the placeholder itself.
    "named_gendered_org": {
        "control": "Member, Men's Engineering Club",
        "female": "Member, Society of Women Engineers",
    },
}


def with_name(resume: str, name: str) -> str:
    """Prepend a name header, as a conventional resume would have."""
    return f"{name}\n{resume}"


def with_line(resume: str, line: str) -> str:
    return f"{resume.rstrip()}\n{line}\n"


@dataclass
class AuditRow:
    condition: str  # e.g. "names:white_male" or "hobbies:female_coded"
    reference: str  # what it is compared with
    mean_delta: float
    ci: tuple[float, float]
    flip_rate: float
    n: int


def _bootstrap_mean(delta: np.ndarray, groups: np.ndarray, n_boot: int = 1000, seed: int = 13) -> tuple[float, float]:
    keys = np.unique(groups)
    idx = {k: np.where(groups == k)[0] for k in keys}
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(keys, size=len(keys), replace=True)
        means[b] = delta[np.concatenate([idx[k] for k in pick])].mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def summarise(
    scores: dict[str, np.ndarray],
    decisions: dict[str, np.ndarray],
    reference: dict[str, str],
    groups: np.ndarray,
) -> list[AuditRow]:
    """Paired score differences ``condition - reference`` with JD-cluster bootstrap CIs."""
    rows = []
    for cond, ref in reference.items():
        delta = scores[cond] - scores[ref]
        lo, hi = _bootstrap_mean(delta, groups)
        flips = float((decisions[cond] != decisions[ref]).mean())
        rows.append(AuditRow(cond, ref, float(delta.mean()), (lo, hi), flips, len(delta)))
    return rows


def name_gap(scores: dict[str, np.ndarray], groups: np.ndarray) -> dict[str, float]:
    """Largest pairwise gap in cell-mean score, plus white_male minus each other cell."""
    cells = {k.split(":", 1)[1]: v for k, v in scores.items() if k.startswith("names:")}
    means = {c: float(v.mean()) for c, v in cells.items()}
    out = {"max_pairwise_gap": max(means.values()) - min(means.values())}
    base = means.get("white_male")
    if base is not None:
        out.update({f"white_male_minus_{c}": base - m for c, m in means.items() if c != "white_male"})
    return out


def permutation_pvalue(a: np.ndarray, b: np.ndarray, n_perm: int = 5000, seed: int = 13) -> float:
    """Two-sided paired permutation (sign-flip) test on the mean of ``a - b``."""
    d = a - b
    obs = abs(d.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_perm, len(d)))
    perm = np.abs((signs * d).mean(1))
    return float((np.sum(perm >= obs) + 1) / (n_perm + 1))


Scorer = Callable[[list[str], list[str]], tuple[np.ndarray, np.ndarray]]
