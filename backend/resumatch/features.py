"""Document preparation and pair-level features.

One code path produces both the feature vector fed to the classifier and the
evidence shown to the user, so an explanation can never describe a signal the
model did not use.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .embed import Embedder
from .experience import education_level, required_education, required_years, resume_years
from .jobreq import Requirement, parse_requirements
from .redact import RedactionReport, redact
from .skills import SkillLexicon
from .text import STOPWORDS, normalize, split_sentences, tokenize

# Fixed a-priori similarity cut-offs (chosen from training-split probes only).
COVER_STRONG = 0.50
COVER_WEAK = 0.40

FEATURE_GROUPS: dict[str, list[str]] = {
    "lexical": ["lex_tfidf_cos", "lex_bm25", "lex_idf_overlap"],
    "semantic": [
        "sem_doc_cos_full",
        "sem_doc_cos_req",
        "sem_head_cos",
        "sem_cov_mean",
        "sem_cov_required",
        "sem_cov_preferred",
        "sem_cov_p25",
        "sem_cov_min",
        "sem_frac_strong",
        "sem_frac_weak",
    ],
    "skills": [
        "skill_cov_required",
        "skill_cov_all",
        "skill_jaccard",
        "skill_n_shared",
        "skill_n_missing_required",
    ],
    "experience": ["exp_gap", "exp_meets", "edu_gap", "edu_meets"],
}
# Attributes of only one document. They let a model memorise "this resume tends to be a
# good fit" or "this JD is easy", which inflates scores when resumes recur across splits
# (as they do in the public benchmark). Excluded from the model; kept for the leakage ablation.
IDENTITY_FEATURES: list[str] = [
    "exp_res_years",
    "edu_res",
    "skill_n_resume",
    "exp_req_years",
    "edu_req",
    "skill_n_jd",
    "exp_has_req",
]
FEATURE_NAMES: list[str] = [f for names in FEATURE_GROUPS.values() for f in names]
ALL_FEATURES: list[str] = FEATURE_NAMES + IDENTITY_FEATURES


@dataclass
class CorpusStats:
    """Corpus statistics. Fitted on training documents only."""

    tfidf: TfidfVectorizer
    bm25_idf: dict[str, float]
    bm25_avgdl: float
    skill_idf: dict[str, float]
    default_skill_idf: float

    @classmethod
    def fit(cls, resumes: list[str], jds: list[str], lexicon: SkillLexicon) -> "CorpusStats":
        small = len(resumes) + len(jds) < 10  # tiny corpora (demos, tests): keep every term
        tfidf = TfidfVectorizer(
            stop_words="english", sublinear_tf=True, min_df=1 if small else 2, max_df=1.0 if small else 0.9
        )
        tfidf.fit(list(resumes) + list(jds))
        n = len(resumes)
        df: dict[str, int] = {}
        total_len = 0
        for text in resumes:
            toks = tokenize(text)
            total_len += len(toks)
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        idf = {t: math.log((n - c + 0.5) / (c + 0.5) + 1.0) for t, c in df.items()}
        docs = list(resumes) + list(jds)
        sdf: dict[str, int] = {}
        for text in docs:
            for s in set(lexicon.find(text)):
                sdf[s] = sdf.get(s, 0) + 1
        nd = len(docs)
        skill_idf = {s: math.log((nd + 1) / (c + 1)) + 1.0 for s, c in sdf.items()}
        return cls(tfidf, idf, total_len / max(1, n), skill_idf, math.log(nd + 1) + 1.0)


@dataclass
class PreparedResume:
    raw_text: str
    text: str
    sentences: list[str]
    sent_emb: np.ndarray
    doc_emb: np.ndarray
    head_emb: np.ndarray
    skills: dict[str, list[int]]
    years: float
    edu: int
    tokens: list[str]
    redaction: RedactionReport
    tfidf_vec: object = None


@dataclass
class PreparedJob:
    raw_text: str
    text: str
    sentences: list[str]
    sent_emb: np.ndarray
    requirements: list[Requirement]
    req_emb: np.ndarray
    doc_emb_full: np.ndarray
    doc_emb_req: np.ndarray
    head_emb: np.ndarray
    skill_kind_weight: dict[str, float]
    years_required: float
    edu_required: int
    tokens: list[str]
    tfidf_vec: object = None


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def _head(text: str, words: int = 40) -> str:
    return " ".join(text.split()[:words])


def prepare_resumes(
    texts: list[str],
    embedder: Embedder,
    lexicon: SkillLexicon,
    *,
    do_redact: bool = True,
    known_names: list[list[str]] | None = None,
    as_of: date | None = None,
) -> list[PreparedResume]:
    cleaned: list[tuple[str, RedactionReport]] = []
    for i, raw in enumerate(texts):
        if do_redact:
            kn = known_names[i] if known_names else None
            red, rep = redact(raw, known_names=kn)
        else:
            red, rep = raw, RedactionReport()
        cleaned.append((normalize(red), rep))
    sents = [split_sentences(c) or [c[:300] or "empty"] for c, _ in cleaned]
    heads = [_head(c) or "empty" for c, _ in cleaned]
    flat = [s for ss in sents for s in ss] + heads
    emb = embedder.encode(flat)
    out: list[PreparedResume] = []
    pos = 0
    for (clean, rep), raw, ss, head in zip(cleaned, texts, sents, heads):
        se = emb[pos : pos + len(ss)]
        pos += len(ss)
        out.append(
            PreparedResume(
                raw_text=raw,
                text=clean,
                sentences=ss,
                sent_emb=se,
                doc_emb=_unit(se.mean(0)),
                head_emb=np.zeros(0),  # filled below once head embeddings are sliced
                skills=lexicon.find_by_sentence(ss),
                years=resume_years(clean, as_of),
                edu=education_level(clean),
                tokens=tokenize(clean),
                redaction=rep,
            )
        )
    head_emb = emb[pos:]
    for r, h in zip(out, head_emb):
        r.head_emb = h
    return out


def prepare_jobs(texts: list[str], embedder: Embedder, lexicon: SkillLexicon) -> list[PreparedJob]:
    cleaned = [normalize(t) for t in texts]
    all_sents = [split_sentences(c) or [c[:300] or "empty"] for c in cleaned]
    reqs = [parse_requirements(c) for c in cleaned]
    heads = [_head(c) or "empty" for c in cleaned]
    flat = [s for ss in all_sents for s in ss] + [r.text for rs in reqs for r in rs] + heads
    emb = embedder.encode(flat)
    out: list[PreparedJob] = []
    pos = 0
    sent_slices = []
    for ss in all_sents:
        sent_slices.append(emb[pos : pos + len(ss)])
        pos += len(ss)
    req_slices = []
    for rs in reqs:
        req_slices.append(emb[pos : pos + len(rs)])
        pos += len(rs)
    head_embs = emb[pos:]
    for raw, clean, ss, rs, se, re_, he in zip(texts, cleaned, all_sents, reqs, sent_slices, req_slices, head_embs):
        w = np.array([r.weight for r in rs], dtype=np.float32)
        skill_w: dict[str, float] = {}
        for r in rs:
            for s in set(lexicon.find(r.text)):
                skill_w[s] = max(skill_w.get(s, 0.0), r.weight)
        out.append(
            PreparedJob(
                raw_text=raw,
                text=clean,
                sentences=ss,
                sent_emb=se,
                requirements=rs,
                req_emb=re_,
                doc_emb_full=_unit(se.mean(0)),
                doc_emb_req=_unit((re_ * w[:, None]).sum(0)) if len(rs) else _unit(se.mean(0)),
                head_emb=he,
                skill_kind_weight=skill_w,
                years_required=required_years(clean),
                edu_required=required_education(clean),
                tokens=tokenize(clean),
            )
        )
    return out


@dataclass
class RequirementMatch:
    requirement: Requirement
    sentence_index: int
    similarity: float


@dataclass
class PairAnalysis:
    """Everything the explanation needs, derived once per (resume, JD)."""

    matches: list[RequirementMatch]
    matched_skills: dict[str, int]  # skill -> resume sentence index
    missing_skills: list[str]
    features: dict[str, float] = field(default_factory=dict)


def analyse_pair(r: PreparedResume, j: PreparedJob, stats: CorpusStats) -> PairAnalysis:
    sim = j.req_emb @ r.sent_emb.T  # (n_req, n_sent)
    best_idx = sim.argmax(1)
    best = sim.max(1)
    weights = np.array([q.weight for q in j.requirements], dtype=np.float32)
    kinds = np.array([q.kind for q in j.requirements])
    matches = [RequirementMatch(q, int(i), float(s)) for q, i, s in zip(j.requirements, best_idx, best)]

    def wmean(mask: np.ndarray, fallback: float) -> float:
        return float((best[mask] * weights[mask]).sum() / weights[mask].sum()) if mask.any() else fallback

    cov_mean = float((best * weights).sum() / weights.sum())
    f: dict[str, float] = {
        "sem_doc_cos_full": float(r.doc_emb @ j.doc_emb_full),
        "sem_doc_cos_req": float(r.doc_emb @ j.doc_emb_req),
        "sem_head_cos": float(r.head_emb @ j.head_emb),
        "sem_cov_mean": cov_mean,
        "sem_cov_required": wmean(kinds == "required", cov_mean),
        "sem_cov_preferred": wmean(kinds == "preferred", cov_mean),
        "sem_cov_p25": float(np.percentile(best, 25)),
        "sem_cov_min": float(best.min()),
        "sem_frac_strong": float((best >= COVER_STRONG).mean()),
        "sem_frac_weak": float((best >= COVER_WEAK).mean()),
    }

    # Lexical features
    if r.tfidf_vec is None:
        r.tfidf_vec = stats.tfidf.transform([r.text])
    if j.tfidf_vec is None:
        j.tfidf_vec = stats.tfidf.transform([j.text])
    f["lex_tfidf_cos"] = float(r.tfidf_vec.multiply(j.tfidf_vec).sum())  # type: ignore[attr-defined]
    k1, b = 1.5, 0.75
    tf_counts: dict[str, int] = {}
    for t in r.tokens:
        tf_counts[t] = tf_counts.get(t, 0) + 1
    norm = k1 * (1 - b + b * len(r.tokens) / max(1.0, stats.bm25_avgdl))
    q_terms = {t for t in j.tokens if t not in STOPWORDS}
    num = den = 0.0
    overlap = total = 0.0
    for t in q_terms:
        w = stats.bm25_idf.get(t, 0.0)
        den += w
        total += w
        c = tf_counts.get(t, 0)
        if c:
            num += w * c * (k1 + 1) / (c + norm)
            overlap += w
    f["lex_bm25"] = num / den if den else 0.0
    f["lex_idf_overlap"] = overlap / total if total else 0.0

    # Skill features (IDF-weighted, kind-weighted)
    jd_sk = j.skill_kind_weight
    res_sk = set(r.skills)

    def sw(s: str) -> float:
        return stats.skill_idf.get(s, stats.default_skill_idf) * jd_sk[s]

    req_sk = [s for s, w in jd_sk.items() if w >= 0.75] or list(jd_sk)
    tot_all = sum(sw(s) for s in jd_sk)
    tot_req = sum(sw(s) for s in req_sk)
    f["skill_cov_all"] = sum(sw(s) for s in jd_sk if s in res_sk) / tot_all if tot_all else 0.0
    f["skill_cov_required"] = sum(sw(s) for s in req_sk if s in res_sk) / tot_req if tot_req else 0.0
    union = set(jd_sk) | res_sk
    f["skill_jaccard"] = len(set(jd_sk) & res_sk) / len(union) if union else 0.0
    missing = [s for s in req_sk if s not in res_sk]
    f["skill_n_shared"] = math.log1p(len(set(jd_sk) & res_sk))
    f["skill_n_missing_required"] = math.log1p(len(missing))
    f["skill_n_jd"] = math.log1p(len(jd_sk))
    f["skill_n_resume"] = math.log1p(len(res_sk))

    # Experience and education
    has_req = 1.0 if j.years_required > 0 else 0.0
    gap = max(-10.0, min(10.0, r.years - j.years_required))
    f.update(
        {
            "exp_res_years": min(r.years, 40.0),
            "exp_req_years": j.years_required,
            "exp_gap": gap if has_req else 0.0,
            "exp_meets": 1.0 if (not has_req or r.years >= j.years_required) else 0.0,
            "exp_has_req": has_req,
            "edu_res": float(r.edu),
            "edu_req": float(j.edu_required),
            "edu_gap": float(max(-2, min(2, r.edu - j.edu_required))) if j.edu_required else 0.0,
            "edu_meets": 1.0 if (j.edu_required == 0 or r.edu >= j.edu_required) else 0.0,
        }
    )
    matched = {s: r.skills[s][0] for s in jd_sk if s in res_sk}
    missing_sorted = sorted(missing, key=lambda s: -sw(s))
    return PairAnalysis(matches, matched, missing_sorted, f)


def feature_vector(analysis: PairAnalysis, names: list[str] | None = None) -> np.ndarray:
    names = names or FEATURE_NAMES
    return np.array([analysis.features[n] for n in names], dtype=np.float64)
