"""EviMatch API: evidence-grounded, bias-audited resume screening.

Design choices
* Stateless: resumes are parsed in memory and never written to disk or a database.
* Deterministic scoring; an LLM is optional and only rephrases the evidence.
* Every response says what was redacted and which evidence supports the score.
"""

from __future__ import annotations

import secrets
from typing import Any

import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Security, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import config
from engine import get_engine
from llm import llm_narrative
from parser import MAX_BYTES, ResumeParseError, extract_text, looks_like_resume
from resumatch import VERSION
from resumatch.fairness import NAMES, PROXIES, with_line, with_name
from resumatch.model import DECISIONS
from summary import build_summary

app = FastAPI(
    title="EviMatch API",
    version=VERSION,
    description="Evidence-grounded, bias-audited resume-job matching. Decision support only.",
)
limiter = Limiter(key_func=get_remote_address, default_limits=[config.RATE_LIMIT])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
MIN_JD_WORDS = 25


async def require_key(key: str | None = Security(_api_key_header)) -> None:
    if config.API_KEY and not (key and secrets.compare_digest(key, config.API_KEY)):
        raise HTTPException(status_code=403, detail="Invalid or missing API key")


def _read_resume(upload: UploadFile) -> tuple[str, list[str]]:
    data = upload.file.read(MAX_BYTES + 1)
    try:
        text = extract_text(upload.filename or "", data)
    except ResumeParseError as exc:
        raise HTTPException(status_code=422, detail=f"{upload.filename}: {exc}") from exc
    warnings = (
        [] if looks_like_resume(text) else ["The document does not look like a resume; results may be unreliable."]
    )
    return text, warnings


def _check_jd(jd: str) -> str:
    jd = jd.strip()
    if len(jd.split()) < MIN_JD_WORDS:
        raise HTTPException(status_code=422, detail=f"Job description must have at least {MIN_JD_WORDS} words.")
    return jd


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "version": VERSION}


@app.get("/model", dependencies=[Depends(require_key)])
def model_card() -> dict[str, Any]:
    eng = get_engine()
    return {
        "version": VERSION,
        "embedder": eng.embedder.name,
        "head": eng.model.kind,
        "features": eng.model.feature_names,
        "meta": eng.meta,
        "intended_use": "Decision support for screening; a human must review every outcome.",
        "limitations": [
            "Trained on a public benchmark whose labels are noisy and undocumented.",
            "Not validated for non-English resumes, non-technical roles at scale, or any legal compliance regime.",
            "Rule-based redaction removes explicit identifiers only; proxy signals can remain (see /audit).",
        ],
    }


@app.post("/analyze", dependencies=[Depends(require_key)])
def analyze(
    request: Request,
    file: UploadFile = File(...),
    job_description: str = Form(...),
    redact: bool = Form(True),
) -> dict[str, Any]:
    jd = _check_jd(job_description)
    text, warnings = _read_resume(file)
    result = get_engine().analyze(text, jd, do_redact=redact)
    result["summary"] = build_summary(result)
    narrative = llm_narrative(result)
    if narrative:
        result["narrative"] = narrative
    if not redact:
        warnings.append("Redaction is disabled: names and other identity cues were visible to the scorer.")
    result["warnings"] = warnings
    result["filename"] = file.filename
    return result


@app.post("/rank", dependencies=[Depends(require_key)])
def rank(
    request: Request,
    files: list[UploadFile] = File(...),
    job_description: str = Form(...),
    redact: bool = Form(True),
) -> dict[str, Any]:
    if len(files) > config.MAX_RANK_FILES:
        raise HTTPException(status_code=422, detail=f"At most {config.MAX_RANK_FILES} resumes per request.")
    jd = _check_jd(job_description)
    texts: list[str] = []
    names: list[str] = []
    errors: list[dict[str, str]] = []
    for f in files:
        try:
            text, _ = _read_resume(f)
        except HTTPException as exc:
            errors.append({"filename": f.filename or "?", "error": str(exc.detail)})
            continue
        texts.append(text)
        names.append(f.filename or f"resume-{len(names) + 1}")
    ranked: list[dict[str, Any]] = []
    if texts:
        for rec in get_engine().rank(texts, jd, do_redact=redact):
            rec["filename"] = names[rec.pop("index")]
            ranked.append(rec)
        ranked.sort(key=lambda r: -r["fit_score"])
    return {"candidates": ranked, "errors": errors, "redaction_applied": redact}


@app.post("/audit", dependencies=[Depends(require_key)])
def audit(
    request: Request,
    file: UploadFile = File(...),
    job_description: str = Form(...),
    redact: bool = Form(True),
) -> dict[str, Any]:
    """Counterfactual check: how much does the score move if only an irrelevant cue changes?"""
    jd = _check_jd(job_description)
    text, _ = _read_resume(file)
    variants: list[str] = [text]
    cell_idx: dict[str, list[int]] = {}
    for cell, names in NAMES.items():
        for nm in names[:2]:
            cell_idx.setdefault(cell, []).append(len(variants))
            variants.append(with_name(text, nm))
    proxy_idx: list[tuple[str, str, int, int]] = []
    for family, lines in PROXIES.items():
        ctrl_idx = len(variants)
        variants.append(with_line(text, lines["control"]))
        for key, line in lines.items():
            if key == "control":
                continue
            proxy_idx.append((family, key, len(variants), ctrl_idx))
            variants.append(with_line(text, line))
    scores, decisions = get_engine().score_texts(variants, jd, do_redact=redact)
    cells = {c: float(np.mean(scores[i])) for c, i in cell_idx.items()}
    spread = max(cells.values()) - min(cells.values())
    proxies = [
        {
            "cue": f"{fam}:{key}",
            "reference": f"{fam}:control",
            "score_change": round(float(scores[i] - scores[j]), 2),
            "decision_changed": bool(decisions[i] != decisions[j]),
        }
        for fam, key, i, j in proxy_idx
    ]
    return {
        "redaction_applied": redact,
        "baseline_score": round(float(scores[0]), 1),
        "name_cell_scores": {c: round(v, 2) for c, v in cells.items()},
        "name_spread": round(spread, 2),
        "proxy_cues": proxies,
        "decision_at_baseline": DECISIONS[int(decisions[0])],
        "interpretation": (
            "A spread of 0 across name groups is expected when redaction is on; non-zero proxy changes show "
            "residual sensitivity that redaction does not remove."
        ),
    }
