"""E5: how much labelled data does the supervised head need?

Doubly-disjoint folds (S2). Corpus statistics are fitted on the whole training
portion of a fold (they are unsupervised); only the supervised head is trained
on a random subset of training *job descriptions*.

    .venv/bin/python -I research/run_learning_curve.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script dir

import numpy as np
import pandas as pd
from common import SEED, doubly_disjoint_folds, load_data, macro_f1, save_json
from modeling import MINILM, build_features, fit_thresholds, make_embedder, pair_embeddings, select_model

from resumatch import FEATURE_NAMES, FitModel
from resumatch.features import ALL_FEATURES

FRACTIONS = [0.05, 0.1, 0.2, 0.4, 0.7, 1.0]
REPEATS = 3


def main() -> None:
    train_df, test_df = load_data()
    pooled = pd.concat([train_df, test_df], ignore_index=True)
    emb = make_embedder(MINILM, 128)
    emb256 = make_embedder(MINILM, 256)
    cols = [ALL_FEATURES.index(n) for n in FEATURE_NAMES]
    res: dict[str, dict[float, list[float]]] = {s: {f: [] for f in FRACTIONS} for s in ("M3", "B6", "B3_threshold")}
    sizes: dict[float, list[int]] = {f: [] for f in FRACTIONS}
    t0 = time.time()
    for k, (a, b) in enumerate(doubly_disjoint_folds(pooled)):
        tr, te = pooled.iloc[a].reset_index(drop=True), pooled.iloc[b].reset_index(drop=True)
        built = build_features(tr, {"train": tr, "test": te}, emb)
        Xtr, Xte = built.X["train"][:, cols], built.X["test"][:, cols]
        Etr, Ete = pair_embeddings(tr, emb256), pair_embeddings(te, emb256)
        cos_tr, cos_te = Etr[:, -1], Ete[:, -1]
        y_tr, y_te = tr["y"].to_numpy(), te["y"].to_numpy()
        jids = np.array(sorted(tr["jid"].unique()))
        for frac in FRACTIONS:
            for rep in range(REPEATS):
                rng = np.random.default_rng(SEED + 100 * k + rep)
                keep = set(rng.choice(jids, size=max(5, int(round(frac * len(jids)))), replace=False))
                m = tr["jid"].isin(keep).to_numpy()
                if len(np.unique(y_tr[m])) < 3:
                    continue
                sizes[frac].append(int(m.sum()))
                g = tr["jid"].to_numpy()[m]
                model, _ = select_model(Xtr[m], y_tr[m], g, list(FEATURE_NAMES), kinds=("logreg",))
                res["M3"][frac].append(macro_f1(y_te, model.decide(model.predict_proba(Xte))))
                m6 = FitModel("logreg", [f"e{i}" for i in range(Etr.shape[1])], C=0.001).fit(Etr[m], y_tr[m])
                res["B6"][frac].append(macro_f1(y_te, m6.decide(m6.predict_proba(Ete))))
                t1, t2 = fit_thresholds(cos_tr[m], y_tr[m])
                res["B3_threshold"][frac].append(macro_f1(y_te, np.digitize(cos_te, [t1, t2])))
        print(f"fold {k} done ({time.time() - t0:.0f}s)", flush=True)
    out = {
        "fractions": FRACTIONS,
        "mean_train_pairs": {str(f): float(np.mean(v)) for f, v in sizes.items()},
        "macro_f1": {
            s: {str(f): {"mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)), "n": len(v)} for f, v in d.items()}
            for s, d in res.items()
        },
    }
    save_json("learning_curve.json", out)
    for s, d in out["macro_f1"].items():
        print(s, {f: round(v["mean"], 3) for f, v in d.items()})


if __name__ == "__main__":
    main()
