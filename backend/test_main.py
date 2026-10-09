"""API contract tests. The engine is built from scratch with a lexical stand-in embedder."""

import io
from datetime import date

import numpy as np
import pytest
from fastapi.testclient import TestClient

import config
import engine
from main import app
from resumatch import CorpusStats, EviMatch, FitModel, HashingEmbedder, SkillLexicon, redact
from resumatch.features import FEATURE_NAMES
from resumatch.text import normalize

RESUME = (
    "Alex Morgan\nalex@example.com | 555-123-4567\n"
    "Summary 6 years of experience as a backend engineer. He built REST APIs in Python and FastAPI. "
    "Deployed services with Docker and Kubernetes on AWS.\n"
    "Skills: Python, SQL, Docker, Kubernetes, AWS, PostgreSQL\n"
    "Experience 03/2018 to Present Senior Engineer. Bachelor of Science, Northfield State University.\n"
)
JD = (
    "Backend Engineer. Requirements: 4+ years of experience building REST APIs in Python. "
    "Experience with Docker, Kubernetes and AWS is required. Bachelor's degree in Computer Science. "
    "Preferred: PostgreSQL experience is a plus. We offer health insurance and 401k."
)


@pytest.fixture(autouse=True)
def _engine():
    lex = SkillLexicon.from_seed()
    stats = CorpusStats.fit([normalize(redact(RESUME)[0])], [normalize(JD)], lex)
    X = np.random.default_rng(0).normal(size=(90, len(FEATURE_NAMES)))
    model = FitModel("logreg", FEATURE_NAMES).fit(X, np.arange(90) % 3)
    engine.set_engine(EviMatch(HashingEmbedder(128), lex, stats, model, {"note": "test"}, as_of=date(2024, 7, 1)))
    config.API_KEY = ""
    yield
    engine.set_engine(None)


client = TestClient(app)


def _files(text=RESUME, name="cv.txt"):
    return {"file": (name, io.BytesIO(text.encode()), "text/plain")}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_analyze_returns_evidence_and_redaction_report():
    r = client.post("/analyze", files=_files(), data={"job_description": JD})
    assert r.status_code == 200
    body = r.json()
    for key in ("fit_score", "decision", "requirements", "matching_skills", "missing_skills", "summary", "redaction"):
        assert key in body
    assert body["redaction"]["counts"]["email"] == 1
    assert "Alex Morgan" not in str(body["requirements"])
    assert body["decision"] in ("Shortlist", "Review", "Reject")


def test_analyze_rejects_short_job_description_and_bad_file():
    assert client.post("/analyze", files=_files(), data={"job_description": "too short"}).status_code == 422
    bad = {"file": ("x.exe", io.BytesIO(b"MZ" + b"0" * 100), "application/octet-stream")}
    assert client.post("/analyze", files=bad, data={"job_description": JD}).status_code == 422


def test_name_swap_does_not_change_score_when_redacted():
    a = client.post("/analyze", files=_files(), data={"job_description": JD}).json()["fit_score"]
    b = client.post(
        "/analyze", files=_files(RESUME.replace("Alex Morgan", "Lakisha Washington")), data={"job_description": JD}
    ).json()["fit_score"]
    assert a == b


def test_rank_orders_candidates_and_reports_errors():
    other = (
        "Registered nurse with 8 years of experience in patient care.\nSkills: patient care, phlebotomy\nExperience 2015 to Present Nurse "
        + "word " * 15
    )
    files = [
        ("files", ("a.txt", io.BytesIO(RESUME.encode()), "text/plain")),
        ("files", ("b.txt", io.BytesIO(other.encode()), "text/plain")),
        ("files", ("c.xyz", io.BytesIO(b"nope"), "text/plain")),
    ]
    r = client.post("/rank", files=files, data={"job_description": JD})
    assert r.status_code == 200
    body = r.json()
    assert len(body["candidates"]) == 2 and len(body["errors"]) == 1
    scores = [c["fit_score"] for c in body["candidates"]]
    assert scores == sorted(scores, reverse=True)


def test_audit_name_spread_is_zero_with_redaction_and_reported_without():
    on = client.post("/audit", files=_files(), data={"job_description": JD, "redact": "true"}).json()
    assert on["name_spread"] == 0
    assert any(p["cue"] == "affinity_org:black" for p in on["proxy_cues"])
    off = client.post("/audit", files=_files(), data={"job_description": JD, "redact": "false"}).json()
    assert off["redaction_applied"] is False


def test_api_key_enforced_when_configured():
    config.API_KEY = "secret"
    assert client.get("/model").status_code == 403
    assert client.get("/model", headers={"X-API-Key": "secret"}).status_code == 200
