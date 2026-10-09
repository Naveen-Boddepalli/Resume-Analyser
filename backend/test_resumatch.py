"""Unit tests for the EviMatch core package (no model downloads required)."""

from datetime import date

import numpy as np
import pytest

from resumatch import CorpusStats, EviMatch, FitModel, HashingEmbedder, SkillLexicon, redact
from resumatch.experience import education_level, required_education, required_years, resume_years
from resumatch.features import ALL_FEATURES, FEATURE_NAMES, analyse_pair, prepare_jobs, prepare_resumes
from resumatch.jobreq import parse_requirements
from resumatch.text import normalize, split_sentences, tokenize

PY_RESUME = """Alex Morgan
alex@example.com | 555-123-4567
Summary 6 years of experience as a backend engineer. He built REST APIs in Python and FastAPI.Deployed services with Docker and Kubernetes on AWS.
Skills: Python, SQL, Docker, Kubernetes, AWS, PostgreSQL
Experience 03/2018 to Present Senior Engineer. Bachelor of Science, Northfield State University."""

NURSE_RESUME = """Sam Rivera
Summary Registered nurse with 8 years of experience in patient care, electronic health records and medication administration.
Skills: patient care, EHR, BLS, ACLS, phlebotomy
Experience 01/2015 to Present Staff Nurse. Associate degree in nursing."""

BACKEND_JD = """Backend Engineer. Requirements: 4+ years of experience building REST APIs in Python.
Experience with Docker, Kubernetes and AWS is required. Bachelor's degree in Computer Science.
Preferred: PostgreSQL experience is a plus. We offer health insurance and 401k. Equal opportunity employer."""


def test_normalize_repairs_glued_sentences_but_keeps_dotnet():
    out = normalize("Built APIs.Deployed to AWS. Used ASP.Net and Node.js daily.")
    assert "APIs. Deployed" in out
    assert "ASP.Net" in out and "Node.js" in out


def test_split_sentences_windows_long_runons():
    long = " ".join(["word"] * 100)
    parts = split_sentences(long, max_words=45)
    assert len(parts) == 3 and all(len(p.split()) <= 45 for p in parts)


def test_tokenizer_keeps_technical_tokens():
    toks = tokenize("C++, C#, .NET, Node.js and CI/CD with scikit-learn")
    for t in ("c++", "c#", ".net", "node.js", "ci/cd", "scikit-learn"):
        assert t in toks


def test_redaction_removes_explicit_identifiers_and_counts_them():
    out, rep = redact(PY_RESUME)
    assert "Alex Morgan" not in out and "[NAME]" in out
    assert "alex@example.com" not in out and "555-123-4567" not in out
    assert "Northfield State University" not in out
    assert " He " not in out and "They built" in out
    assert "Python" in out and "Docker" in out  # skills survive
    for kind in ("name", "email", "phone", "institution", "pronoun"):
        assert rep.counts.get(kind, 0) >= 1


def test_redaction_removes_personal_detail_fields_and_gendered_orgs():
    text = "Priya Rao\nDate of Birth: 12 May 1990; Marital Status: Single\nMember, Society of Women Engineers"
    out, rep = redact(text)
    assert "1990" not in out and "Single" not in out
    assert "Women Engineers" not in out
    assert rep.counts["personal_field"] == 2 and rep.counts["gendered_org"] == 1


def test_redaction_uses_known_names_anywhere():
    out, _ = redact("Reference: Jordan Lee will confirm.", known_names=["Jordan Lee"])
    assert "Jordan Lee" not in out


def test_skill_lexicon_matches_aliases_and_case_sensitive_words():
    lex = SkillLexicon.from_seed()
    found = lex.find("Built CI/CD with k8s and Node.js; used MS Excel and C++ daily")
    for s in ("ci/cd", "kubernetes", "node.js", "excel", "c++"):
        assert s in found
    assert "excel" not in lex.find("She will excel in a dynamic team")


def test_requirements_drop_boilerplate_and_label_kinds():
    reqs = parse_requirements(BACKEND_JD)
    texts = " ".join(r.text for r in reqs).lower()
    assert "401k" not in texts and "equal opportunity" not in texts
    kinds = {r.kind for r in reqs}
    assert "required" in kinds and "preferred" in kinds


def test_experience_extraction():
    today = date(2024, 7, 1)
    assert resume_years("05/2017 to Present Analyst; 01/2012 to 04/2017 Associate", today) == pytest.approx(
        12.4, abs=0.1
    )
    assert resume_years("Over 7+ years of experience in data", today) == 7.0
    assert required_years("Minimum 5+ years of experience") == 5.0
    assert education_level("PhD in physics; B.Sc.") == 4
    assert required_education("Bachelor's or Master's degree required") == 2


def _tiny_system():
    emb = HashingEmbedder(128)
    lex = SkillLexicon.from_seed()
    resumes = [PY_RESUME, NURSE_RESUME]
    stats = CorpusStats.fit([normalize(redact(t)[0]) for t in resumes], [normalize(BACKEND_JD)], lex)
    pr = prepare_resumes(resumes, emb, lex, as_of=date(2024, 7, 1))
    pj = prepare_jobs([BACKEND_JD], emb, lex)
    return emb, lex, stats, pr, pj


def test_feature_vector_has_every_declared_feature_and_is_finite():
    _, _, stats, pr, pj = _tiny_system()
    a = analyse_pair(pr[0], pj[0], stats)
    assert set(ALL_FEATURES) <= set(a.features)
    assert all(np.isfinite(v) for v in a.features.values())


def test_relevant_resume_covers_more_requirements_than_irrelevant_one():
    _, _, stats, pr, pj = _tiny_system()
    good = analyse_pair(pr[0], pj[0], stats).features
    bad = analyse_pair(pr[1], pj[0], stats).features
    assert good["skill_cov_all"] > bad["skill_cov_all"]
    assert good["lex_tfidf_cos"] > bad["lex_tfidf_cos"]
    assert good["sem_cov_mean"] > bad["sem_cov_mean"]


def test_pipeline_analysis_schema_and_evidence_grounding():
    emb, lex, stats, pr, pj = _tiny_system()
    rng = np.random.default_rng(0)
    X = np.array([[rng.normal() + (i % 3) for _ in FEATURE_NAMES] for i in range(60)])
    y = np.array([i % 3 for i in range(60)])
    model = FitModel("logreg", FEATURE_NAMES).fit(X, y)
    sys_ = EviMatch(emb, lex, stats, model, as_of=date(2024, 7, 1))
    out = sys_.analyze(PY_RESUME, BACKEND_JD)
    for key in (
        "fit_score",
        "decision",
        "probabilities",
        "requirements",
        "matching_skills",
        "missing_skills",
        "redaction",
    ):
        assert key in out
    assert 0 <= out["fit_score"] <= 100
    assert out["decision"] in ("Shortlist", "Review", "Reject")
    assert abs(sum(out["probabilities"].values()) - 1) < 1e-3
    # every claimed skill match must point to a resume sentence that really mentions it
    for m in out["matching_skills"]:
        assert m["skill"] in SkillLexicon.from_seed().find(m["evidence"])
    # redaction happened and the name never reaches the evidence strings
    assert out["redaction"]["counts"].get("name", 0) >= 1
    assert all("Alex Morgan" not in (r["evidence"] or "") for r in out["requirements"])


def test_redaction_makes_explicit_name_cues_score_invariant():
    emb, lex, stats, _, _ = _tiny_system()
    X = np.random.default_rng(1).normal(size=(60, len(FEATURE_NAMES)))
    model = FitModel("logreg", FEATURE_NAMES).fit(X, np.arange(60) % 3)
    sys_ = EviMatch(emb, lex, stats, model, as_of=date(2024, 7, 1))
    base = sys_.analyze(PY_RESUME, BACKEND_JD)["fit_score"]
    swapped = sys_.analyze(PY_RESUME.replace("Alex Morgan", "Lakisha Washington"), BACKEND_JD)["fit_score"]
    assert base == swapped
