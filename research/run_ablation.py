"""E3: ablation of feature groups, redaction, vocabulary induction and encoder.

Usage::

    .venv/bin/python -I research/run_ablation.py S1
    .venv/bin/python -I research/run_ablation.py S2
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script dir

import numpy as np
import pandas as pd
from common import (
    SEED,
    auc,
    doubly_disjoint_folds,
    load_data,
    macro_f1,
    paired_bootstrap_diff,
    per_jd_ranking,
    save_json,
)
from modeling import BGE, MINILM, build_features, make_embedder, select_model

from resumatch import FEATURE_GROUPS, FEATURE_NAMES
from resumatch.features import ALL_FEATURES
from resumatch.model import fit_score


def variants() -> dict[str, dict]:
    out: dict[str, dict] = {"full": {"names": FEATURE_NAMES}}
    for g, names in FEATURE_GROUPS.items():
        out[f"minus_{g}"] = {"names": [n for n in FEATURE_NAMES if n not in names]}
    for g, names in FEATURE_GROUPS.items():
        out[f"only_{g}"] = {"names": list(names)}
    out["no_redaction"] = {"names": FEATURE_NAMES, "do_redact": False}
    out["no_induced_vocab"] = {"names": FEATURE_NAMES, "induce": False}
    out["bge_encoder"] = {"names": FEATURE_NAMES, "embedder": "bge"}
    return out


def main(split: str) -> None:
    train_df, test_df = load_data()
    if split == "S1":
        folds = [(train_df, test_df)]
    elif split == "DEV":
        jids = np.array(sorted(train_df["jid"].unique()))
        held = set(np.random.default_rng(SEED).choice(jids, size=len(jids) // 5, replace=False))
        m = train_df["jid"].isin(held)
        folds = [(train_df[~m].reset_index(drop=True), train_df[m].reset_index(drop=True))]
    else:
        pooled = pd.concat([train_df, test_df], ignore_index=True)
        folds = [
            (pooled.iloc[a].reset_index(drop=True), pooled.iloc[b].reset_index(drop=True))
            for a, b in doubly_disjoint_folds(pooled)
        ]
    embs = {"minilm": make_embedder(MINILM, 128), "bge": make_embedder(BGE, 128)}
    specs = variants()
    t0 = time.time()
    preds: dict[str, list[np.ndarray]] = {k: [] for k in specs}
    scores: dict[str, list[np.ndarray]] = {k: [] for k in specs}
    tests = []
    for k, (tr, te) in enumerate(folds):
        tests.append(te)
        y_tr, g_tr = tr["y"].to_numpy(), tr["jid"].to_numpy()
        cache: dict[tuple, object] = {}
        for name, spec in specs.items():
            key = (spec.get("do_redact", True), spec.get("induce", True), spec.get("embedder", "minilm"))
            if key not in cache:
                cache[key] = build_features(
                    tr,
                    {"train": tr, "test": te},
                    embs[key[2]],
                    do_redact=key[0],
                    induce=key[1],
                )
            built = cache[key]
            cols = [ALL_FEATURES.index(n) for n in spec["names"]]
            model, _ = select_model(built.X["train"][:, cols], y_tr, g_tr, list(spec["names"]), kinds=("logreg",))  # type: ignore[attr-defined]
            P = model.predict_proba(built.X["test"][:, cols])  # type: ignore[attr-defined]
            preds[name].append(model.decide(P))
            scores[name].append(fit_score(P))
        print(f"[{split}] fold {k} done ({time.time() - t0:.0f}s)", flush=True)
    test = pd.concat(tests, ignore_index=True)
    y = test["y"].to_numpy()
    out: dict = {"split": split, "variants": {}}
    full_pred = np.concatenate(preds["full"])
    rank_full = per_jd_ranking(test, np.concatenate(scores["full"])).set_index("jid")["ndcg10"]
    for name in specs:
        p = np.concatenate(preds[name])
        s = np.concatenate(scores[name])
        rank = per_jd_ranking(test, s).set_index("jid")["ndcg10"]
        rec = {
            "macro_f1": macro_f1(y, p),
            "accuracy": float((y == p).mean()),
            "auc_good": auc(y == 2, s),
            "ndcg10": float(rank.mean()),
            "n_features": len(specs[name]["names"]),
        }
        if name != "full":
            rec["delta_macro_f1_vs_full"] = paired_bootstrap_diff(
                test, lambda idx, p=p: macro_f1(y[idx], p[idx]), lambda idx: macro_f1(y[idx], full_pred[idx]), n_boot=1000
            )
            d = (rank - rank_full).dropna().to_numpy()
            rng = np.random.default_rng(SEED)
            boots = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)])
            rec["delta_ndcg10_vs_full"] = {
                "diff": float(d.mean()),
                "lo": float(np.percentile(boots, 2.5)),
                "hi": float(np.percentile(boots, 97.5)),
            }
        out["variants"][name] = rec
    save_json(f"ablation_{split}.json", out)
    print(f"{'variant':22s} {'F1':>6s} {'dF1':>7s} {'nDCG10':>7s} {'dnDCG':>7s} feats")
    for name, r in out["variants"].items():
        df1 = r.get("delta_macro_f1_vs_full", {}).get("diff", 0.0)
        dn = r.get("delta_ndcg10_vs_full", {}).get("diff", 0.0)
        print(f"{name:22s} {r['macro_f1']:6.3f} {df1:+7.3f} {r['ndcg10']:7.3f} {dn:+7.3f} {r['n_features']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "S2")
