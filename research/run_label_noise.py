"""E7: how much of the label is explained by *which* JD / resume it is?

Reports duplicate-pair disagreement and the share of label variance explained
by JD identity and by resume identity (eta squared), against a permutation null.

    .venv/bin/python -I research/run_label_noise.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script dir

import numpy as np
import pandas as pd
from common import SEED, load_data, save_json


def eta_squared(y: np.ndarray, g: np.ndarray) -> float:
    total = ((y - y.mean()) ** 2).sum()
    between = 0.0
    for k in np.unique(g):
        m = g == k
        between += m.sum() * (y[m].mean() - y.mean()) ** 2
    return float(between / total)


def main() -> None:
    train, test = load_data()
    out: dict = {}
    for name, df in (("train", train), ("test", test), ("pooled", pd.concat([train, test], ignore_index=True))):
        y = df["y"].to_numpy().astype(float)
        rng = np.random.default_rng(SEED)
        entry = {"n_pairs": int(len(df))}
        for key in ("jid", "rid"):
            g = df[key].to_numpy()
            obs = eta_squared(y, g)
            null = [eta_squared(rng.permutation(y), g) for _ in range(200)]
            entry[f"eta2_{key}"] = obs
            entry[f"eta2_{key}_null_mean"] = float(np.mean(null))
            entry[f"n_{key}"] = int(len(np.unique(g)))
        out[name] = entry
    g = train.groupby(["rid", "jid"])["label"].agg(["size", "nunique"])
    d = g[g["size"] > 1]
    out["duplicate_pairs_train"] = {
        "groups": int(len(d)),
        "rows": int(d["size"].sum()),
        "groups_with_conflicting_labels": int((d["nunique"] > 1).sum()),
    }
    out["resume_overlap"] = {
        "test_resumes_seen_in_train": float(test["rid"].isin(set(train["rid"])).mean()),
        "test_jds_seen_in_train": float(test["jid"].isin(set(train["jid"])).mean()),
    }
    save_json("label_noise.json", out)
    for k, v in out.items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()})


if __name__ == "__main__":
    main()
