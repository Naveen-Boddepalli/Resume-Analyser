"""Shared helpers for the EviMatch experiments (data, splits, metrics, bootstrap).

Every script in ``research/`` is run with ``python -I`` from the repository root
so that nothing is imported from the current directory implicitly.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

RAW = ROOT / "data" / "raw" / "resume-job-description-fit"
RESULTS = ROOT / "research" / "results"
CACHE = ROOT / "research" / "cache"
FIGURES = ROOT / "research" / "figures"
AS_OF = date(2024, 7, 1)  # dataset snapshot date; makes "to Present" reproducible
SEED = 13
LABELS = {"No Fit": 0, "Potential Fit": 1, "Good Fit": 2}
CHECKSUMS = {
    "train.csv": "b86fa488a21258015de1750633a9ac410f701ff96bf533f68978dbe3adec6d40",
    "test.csv": "f3c48f4cc3559bf192ebb9c241a30c601b5b8b3eee6f1656dd4d26dfd4b0887a",
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the official split after verifying file checksums."""
    out = []
    for name in ("train.csv", "test.csv"):
        path = RAW / name
        if _sha256(path) != CHECKSUMS[name]:
            raise RuntimeError(f"checksum mismatch for {name}; refusing to run on altered data")
        df = pd.read_csv(path)
        df["y"] = df["label"].map(LABELS).astype(int)
        df["rid"] = df["resume_text"].map(hash_id)
        df["jid"] = df["job_description_text"].map(hash_id)
        df["split"] = name.split(".")[0]
        out.append(df)
    return out[0], out[1]


def hash_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]


def doubly_disjoint_folds(df: pd.DataFrame, k: int = 5, seed: int = SEED) -> list[tuple[np.ndarray, np.ndarray]]:
    """Folds where neither the resume nor the JD of a test pair occurs in training."""
    rng = np.random.default_rng(seed)
    rids = np.array(sorted(df["rid"].unique()))
    jids = np.array(sorted(df["jid"].unique()))
    r_fold = dict(zip(rids, rng.permutation(len(rids)) % k))
    j_fold = dict(zip(jids, rng.permutation(len(jids)) % k))
    rf = df["rid"].map(r_fold).to_numpy()
    jf = df["jid"].map(j_fold).to_numpy()
    folds = []
    for f in range(k):
        test = np.where((rf == f) & (jf == f))[0]
        train = np.where((rf != f) & (jf != f))[0]
        folds.append((train, test))
    return folds


# --------------------------------------------------------------------------- metrics
def macro_f1(y: np.ndarray, p: np.ndarray) -> float:
    f = []
    for c in range(3):
        tp = float(((p == c) & (y == c)).sum())
        fp = float(((p == c) & (y != c)).sum())
        fn = float(((p != c) & (y == c)).sum())
        d = 2 * tp + fp + fn
        f.append(2 * tp / d if d else 0.0)
    return float(np.mean(f))


def per_class_prf(y: np.ndarray, p: np.ndarray) -> dict[str, dict[str, float]]:
    out = {}
    for name, c in LABELS.items():
        tp = float(((p == c) & (y == c)).sum())
        fp = float(((p == c) & (y != c)).sum())
        fn = float(((p != c) & (y == c)).sum())
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        out[name] = {"precision": pr, "recall": rc, "f1": 2 * pr * rc / (pr + rc) if pr + rc else 0.0}
    return out


def confusion(y: np.ndarray, p: np.ndarray) -> list[list[int]]:
    m = np.zeros((3, 3), dtype=int)
    for a, b in zip(y, p):
        m[a, b] += 1
    return m.tolist()


def quadratic_kappa(y: np.ndarray, p: np.ndarray) -> float:
    obs = np.array(confusion(y, p), dtype=float)
    n = obs.sum()
    if n == 0:
        return 0.0
    W = np.array([[(i - j) ** 2 / 4.0 for j in range(3)] for i in range(3)])
    E = np.outer(obs.sum(1), obs.sum(0)) / n
    d = (W * E).sum()
    return float(1 - (W * obs).sum() / d) if d else 0.0


def auc(y_bin: np.ndarray, s: np.ndarray) -> float:
    """ROC-AUC via the rank-sum statistic (ties get average ranks)."""
    y_bin = np.asarray(y_bin).astype(bool)
    n1, n0 = int(y_bin.sum()), int((~y_bin).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = pd.Series(s).rank(method="average").to_numpy()
    return float((order[y_bin].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def average_precision(y_bin: np.ndarray, s: np.ndarray) -> float:
    y_bin = np.asarray(y_bin).astype(bool)
    if y_bin.sum() == 0:
        return float("nan")
    order = np.argsort(-s, kind="stable")
    hits = y_bin[order]
    prec = np.cumsum(hits) / (np.arange(len(hits)) + 1)
    return float((prec * hits).sum() / hits.sum())


def ndcg_at_k(gains: np.ndarray, scores: np.ndarray, k: int) -> float:
    order = np.argsort(-scores, kind="stable")[:k]
    disc = 1.0 / np.log2(np.arange(2, len(order) + 2))
    dcg = float(((2.0 ** gains[order] - 1) * disc).sum())
    ideal = np.sort(gains)[::-1][:k]
    idcg = float(((2.0**ideal - 1) * (1.0 / np.log2(np.arange(2, len(ideal) + 2)))).sum())
    return dcg / idcg if idcg > 0 else float("nan")


def per_jd_ranking(df: pd.DataFrame, scores: np.ndarray, min_candidates: int = 5) -> pd.DataFrame:
    """nDCG@5, nDCG@10 and AP (Good Fit as relevant) for every JD."""
    rows = []
    tmp = df.assign(_s=scores)
    rng = np.random.default_rng(SEED)
    for jid, g in tmp.groupby("jid"):
        if len(g) < min_candidates:
            continue
        # Random (seeded) tie-breaking: the file order of the benchmark is not random.
        perm = rng.permutation(len(g))
        y = g["y"].to_numpy()[perm]
        s = g["_s"].to_numpy()[perm]
        rows.append(
            {
                "jid": jid,
                "n": len(g),
                "ndcg5": ndcg_at_k(y.astype(float), s, 5),
                "ndcg10": ndcg_at_k(y.astype(float), s, 10),
                "ap_good": average_precision(y == 2, s),
            }
        )
    return pd.DataFrame(rows)


def brier(y: np.ndarray, P: np.ndarray) -> float:
    onehot = np.eye(3)[y]
    return float(((P - onehot) ** 2).sum(1).mean())


def ece(y_bin: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    tot = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            tot += m.mean() * abs(y_bin[m].mean() - p[m].mean())
    return float(tot)


def classification_report(y: np.ndarray, pred: np.ndarray, score: np.ndarray) -> dict:
    return {
        "n": int(len(y)),
        "accuracy": float((y == pred).mean()),
        "macro_f1": macro_f1(y, pred),
        "qwk": quadratic_kappa(y, pred),
        "auc_good_vs_rest": auc(y == 2, score),
        "auc_nofit_vs_rest": auc(y > 0, score),
        "ap_good": average_precision(y == 2, score),
        "per_class": per_class_prf(y, pred),
        "confusion": confusion(y, pred),
    }


def bootstrap_by_jd(
    df: pd.DataFrame,
    stat_fn,
    n_boot: int = 2000,
    seed: int = SEED,
) -> tuple[float, float, float]:
    """Point estimate and 95% percentile CI, resampling job descriptions.

    ``stat_fn(index_array) -> float`` receives positional indices into ``df``.
    """
    groups = df.groupby("jid").indices
    keys = list(groups)
    point = float(stat_fn(np.arange(len(df))))
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, len(keys), len(keys))
        idx = np.concatenate([groups[keys[i]] for i in pick])
        vals[b] = stat_fn(idx)
    lo, hi = np.nanpercentile(vals, [2.5, 97.5])
    return point, float(lo), float(hi)


def paired_bootstrap_diff(
    df: pd.DataFrame,
    stat_a,
    stat_b,
    n_boot: int = 2000,
    seed: int = SEED,
) -> dict[str, float]:
    """Paired difference (a - b), resampling JDs; reports CI and a two-sided p."""
    groups = df.groupby("jid").indices
    keys = list(groups)
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, len(keys), len(keys))
        idx = np.concatenate([groups[keys[i]] for i in pick])
        diffs[b] = stat_a(idx) - stat_b(idx)
    point = float(stat_a(np.arange(len(df))) - stat_b(np.arange(len(df))))
    lo, hi = np.nanpercentile(diffs, [2.5, 97.5])
    p = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
    return {"diff": point, "lo": float(lo), "hi": float(hi), "p_two_sided": float(min(1.0, p))}


# --------------------------------------------------------------------------- provenance
def provenance() -> dict:
    def _git(*args: str) -> str:
        try:
            return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()  # nosec B603 B607
        except Exception:
            return "unknown"

    import sklearn
    import torch

    return {
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "sklearn": sklearn.__version__,
        "torch": torch.__version__,
        "seed": SEED,
        "as_of": AS_OF.isoformat(),
    }


def save_json(name: str, payload: dict) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / name
    payload = {"provenance": provenance(), **payload}
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=1, default=float)
    return path
