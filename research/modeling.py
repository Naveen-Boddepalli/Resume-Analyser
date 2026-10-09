"""Feature building, baselines and model selection used by the experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from common import AS_OF, CACHE, SEED, macro_f1
from sklearn.model_selection import GroupKFold

from resumatch import CachedEmbedder, CorpusStats, FitModel, SentenceTransformerEmbedder, SkillLexicon
from resumatch.features import ALL_FEATURES, analyse_pair, prepare_jobs, prepare_resumes
from resumatch.skills import induce_vocabulary

MINILM = "sentence-transformers/all-MiniLM-L6-v2"
BGE = "BAAI/bge-small-en-v1.5"


def make_embedder(model: str = MINILM, max_seq_length: int = 128) -> CachedEmbedder:
    return CachedEmbedder(SentenceTransformerEmbedder(model, max_seq_length), CACHE / "emb")


@dataclass
class Built:
    lexicon: SkillLexicon
    stats: CorpusStats
    X: dict[str, np.ndarray]  # name -> (n_pairs, n_features) for each evaluated frame
    prepared_resumes: dict[str, object]
    prepared_jobs: dict[str, object]


def build_features(
    train: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    embedder: CachedEmbedder,
    *,
    do_redact: bool = True,
    induce: bool = True,
    min_df: int = 8,
) -> Built:
    """Fit corpus statistics on ``train`` only and featurise every frame."""
    tr_r = train.drop_duplicates("rid").set_index("rid")["resume_text"]
    tr_j = train.drop_duplicates("jid").set_index("jid")["job_description_text"]
    lexicon = SkillLexicon.from_seed()
    if induce:
        extra = induce_vocabulary(list(tr_r.values), lexicon, min_df=min_df)
        lexicon = SkillLexicon.from_seed(extra)
    # Corpus statistics use the same (redacted) text the model will see.
    from resumatch.redact import redact
    from resumatch.text import normalize

    def view(t: str) -> str:
        return normalize(redact(t)[0] if do_redact else t)

    stats = CorpusStats.fit([view(t) for t in tr_r.values], [normalize(t) for t in tr_j.values], lexicon)

    all_frames = pd.concat(frames.values())
    ur = all_frames.drop_duplicates("rid").set_index("rid")["resume_text"]
    uj = all_frames.drop_duplicates("jid").set_index("jid")["job_description_text"]
    pr = dict(zip(ur.index, prepare_resumes(list(ur.values), embedder, lexicon, do_redact=do_redact, as_of=AS_OF)))
    pj = dict(zip(uj.index, prepare_jobs(list(uj.values), embedder, lexicon)))
    X = {}
    for name, df in frames.items():
        rows = []
        for rid, jid in zip(df["rid"], df["jid"]):
            f = analyse_pair(pr[rid], pj[jid], stats).features  # type: ignore[arg-type]
            rows.append([f[n] for n in ALL_FEATURES])
        X[name] = np.asarray(rows, dtype=np.float64)
    embedder.save()
    return Built(lexicon, stats, X, pr, pj)


def doc_cosine(df: pd.DataFrame, embedder: CachedEmbedder) -> np.ndarray:
    """Standard practice: embed each whole document (truncated by the encoder)."""
    u = embedder.encode(df["resume_text"].tolist())
    v = embedder.encode(df["job_description_text"].tolist())
    embedder.save()
    return (u * v).sum(1)


def pair_embeddings(df: pd.DataFrame, embedder: CachedEmbedder) -> np.ndarray:
    u = embedder.encode(df["resume_text"].tolist())
    v = embedder.encode(df["job_description_text"].tolist())
    embedder.save()
    return np.hstack([u * v, np.abs(u - v), (u * v).sum(1, keepdims=True)])


def fit_thresholds(score: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Two cut points on a scalar score that maximise macro-F1 on training data."""
    grid = np.quantile(score, np.linspace(0.05, 0.95, 91))
    best, arg = -1.0, (grid[0], grid[-1])
    for i, t1 in enumerate(grid):
        for t2 in grid[i + 1 :]:
            f = macro_f1(y, np.digitize(score, [t1, t2]))
            if f > best:
                best, arg = f, (float(t1), float(t2))
    return arg


def candidates() -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = [("logreg", {"C": c}) for c in (0.003, 0.01, 0.03, 0.1, 0.3, 1.0)]
    out += [("gbm", {"max_depth": d, "max_iter": it}) for d in (2, 3) for it in (100, 200)]
    return out


def select_model(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    feature_names: list[str],
    kinds: tuple[str, ...] = ("logreg", "gbm"),
    seed: int = SEED,
) -> tuple[FitModel, dict]:
    """5-fold grouped CV; pick the simplest model within one SE of the best."""
    cand = [c for c in candidates() if c[0] in kinds]
    n_splits = min(5, len(np.unique(groups)))
    folds = list(GroupKFold(n_splits).split(X, y, groups))
    table = []
    for kind, params in cand:
        scores = []
        for tr, va in folds:
            m = FitModel(kind, feature_names, seed=seed, **params).fit(X[tr], y[tr])
            scores.append(macro_f1(y[va], m.decide(m.predict_proba(X[va]))))
        scores_a = np.array(scores)
        table.append(
            {
                "kind": kind,
                "params": params,
                "mean": float(scores_a.mean()),
                "se": float(scores_a.std(ddof=1) / np.sqrt(len(scores_a))),
            }
        )
    best = max(table, key=lambda r: r["mean"])
    threshold = best["mean"] - best["se"]
    # candidates() is ordered simplest -> most complex
    chosen = next(r for r in table if r["mean"] >= threshold)
    model = FitModel(chosen["kind"], feature_names, seed=seed, **chosen["params"]).fit(X, y)
    return model, {"cv": table, "chosen": chosen, "best": best}
