"""End-to-end EviMatch pipeline: redact -> prepare -> features -> score -> explain."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from .embed import Embedder
from .features import (
    COVER_STRONG,
    COVER_WEAK,
    FEATURE_GROUPS,
    CorpusStats,
    PairAnalysis,
    PreparedJob,
    PreparedResume,
    analyse_pair,
    feature_vector,
    prepare_jobs,
    prepare_resumes,
)
from .model import CLASSES, DECISIONS, FitModel
from .skills import SkillLexicon

VERSION = "1.0.0"
DEFAULT_ARTIFACT = Path(__file__).parent / "artifacts" / "evimatch.joblib"


def _group_of(feature: str) -> str:
    for g, names in FEATURE_GROUPS.items():
        if feature in names:
            return g
    return "other"


class EviMatch:
    def __init__(
        self,
        embedder: Embedder,
        lexicon: SkillLexicon,
        stats: CorpusStats,
        model: FitModel,
        meta: dict[str, Any] | None = None,
        as_of: date | None = None,
    ):
        self.embedder = embedder
        self.lexicon = lexicon
        self.stats = stats
        self.model = model
        self.meta = meta or {}
        self.as_of = as_of

    # ---- batch API used by experiments -------------------------------------------------
    def prepare(
        self, resumes: list[str], jds: list[str], *, do_redact: bool = True
    ) -> tuple[list[PreparedResume], list[PreparedJob]]:
        return (
            prepare_resumes(resumes, self.embedder, self.lexicon, do_redact=do_redact, as_of=self.as_of),
            prepare_jobs(jds, self.embedder, self.lexicon),
        )

    def features_for(self, r: PreparedResume, j: PreparedJob) -> tuple[np.ndarray, PairAnalysis]:
        a = analyse_pair(r, j, self.stats)
        return feature_vector(a, self.model.feature_names), a

    # ---- single-pair API used by the service ---------------------------------------------
    def analyze(
        self,
        resume_text: str,
        jd_text: str,
        *,
        known_names: list[str] | None = None,
        do_redact: bool = True,
        max_requirements: int = 12,
    ) -> dict[str, Any]:
        r = prepare_resumes(
            [resume_text],
            self.embedder,
            self.lexicon,
            do_redact=do_redact,
            known_names=[known_names or []],
            as_of=self.as_of,
        )[0]
        j = prepare_jobs([jd_text], self.embedder, self.lexicon)[0]
        x, a = self.features_for(r, j)
        proba = self.model.predict_proba(x[None, :])[0]
        decision = int(self.model.decide(proba)[0])
        score = float(self.model.score(x[None, :])[0])
        occ = self.model.occlusion(x)
        drivers = sorted(occ.items(), key=lambda kv: -abs(kv[1]))[:8]

        reqs = []
        for m in sorted(a.matches, key=lambda m: (-m.requirement.weight, -m.similarity)):
            status = "met" if m.similarity >= COVER_STRONG else ("partial" if m.similarity >= COVER_WEAK else "unmet")
            reqs.append(
                {
                    "requirement": m.requirement.text,
                    "kind": m.requirement.kind,
                    "status": status,
                    "similarity": round(m.similarity, 3),
                    "evidence": r.sentences[m.sentence_index] if status != "unmet" else None,
                }
            )
        return {
            "fit_score": round(score, 1),
            "decision": DECISIONS[decision],
            "probabilities": {c: round(float(p), 4) for c, p in zip(CLASSES, proba)},
            "requirements": reqs[:max_requirements],
            "requirement_counts": {s: sum(1 for q in reqs if q["status"] == s) for s in ("met", "partial", "unmet")},
            "matching_skills": [{"skill": s, "evidence": r.sentences[i]} for s, i in sorted(a.matched_skills.items())],
            "missing_skills": a.missing_skills[:15],
            "experience": {
                "candidate_years": round(r.years, 1),
                "required_years": j.years_required,
                "meets": bool(a.features["exp_meets"]),
            },
            "education": {
                "candidate_level": int(r.edu),
                "required_level": int(j.edu_required),
                "meets": bool(a.features["edu_meets"]),
            },
            "drivers": [
                {"feature": n, "group": _group_of(n), "effect": round(v, 2)} for n, v in drivers if abs(v) > 0.05
            ],
            "group_effects": {g: round(v, 2) for g, v in self.model.group_contributions(x).items()},
            "redaction": {"applied": do_redact, "counts": r.redaction.counts},
            "model": {"version": VERSION, "embedder": self.embedder.name, **self.meta},
        }

    # ---- persistence -------------------------------------------------------------------------
    def save(self, path: str | Path = DEFAULT_ARTIFACT) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "lexicon": self.lexicon.entries,
                "stats": self.stats,
                "model": self.model,
                "meta": self.meta,
                "embedder_name": self.embedder.name,
                "as_of": self.as_of,
            },
            path,
            compress=3,
        )

    @classmethod
    def load(cls, embedder: Embedder, path: str | Path = DEFAULT_ARTIFACT) -> "EviMatch":
        blob = joblib.load(path)  # nosec B301 - trusted local artefact produced by this repo
        return cls(
            embedder,
            SkillLexicon(blob["lexicon"]),
            blob["stats"],
            blob["model"],
            blob["meta"],
            blob.get("as_of"),
        )
