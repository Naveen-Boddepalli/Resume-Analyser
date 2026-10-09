"""Train the deployable EviMatch artefact on all labelled pairs (train + test).

The reported experimental numbers never use this artefact: they come from the
S1/S2 protocols in which the evaluated pairs are held out. The shipped model
uses every labelled pair because that is what a deployment should do.

    .venv/bin/python -I research/train_artifact.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script dir

import pandas as pd
from common import AS_OF, ROOT, load_data, provenance
from modeling import MINILM, build_features, make_embedder, select_model

from resumatch import FEATURE_NAMES, EviMatch
from resumatch.features import ALL_FEATURES


def main() -> None:
    train, test = load_data()
    pooled = pd.concat([train, test], ignore_index=True)
    emb = make_embedder(MINILM, 128)
    # Deployed configuration = ablation row "no_induced_vocab": induction did not change accuracy
    # (E3) but added noisy terms to user-facing skill lists, so the shipped lexicon is the seed only.
    built = build_features(pooled, {"all": pooled}, emb, induce=False)
    cols = [ALL_FEATURES.index(n) for n in FEATURE_NAMES]
    model, rep = select_model(
        built.X["all"][:, cols], pooled["y"].to_numpy(), pooled["jid"].to_numpy(), list(FEATURE_NAMES)
    )
    meta = {
        "trained_on": "cnamuangtoun/resume-job-description-fit (train+test, 8,000 pairs)",
        "head": rep["chosen"]["kind"],
        "head_params": rep["chosen"]["params"],
        "cv_macro_f1_jd_grouped_optimistic": round(rep["chosen"]["mean"], 4),
        "expected_performance": "see paper/results: doubly-disjoint macro-F1 about 0.47 (95% CI in research/results/main_S2.json)",
        "vocabulary_terms": len(built.lexicon),
    }
    system = EviMatch(emb, built.lexicon, built.stats, model, meta, as_of=None)
    path = ROOT / "backend" / "resumatch" / "artifacts" / "evimatch.joblib"
    system.save(path)
    with open(path.with_suffix(".json"), "w") as fh:
        json.dump(
            {
                "meta": meta,
                "cv": rep["cv"],
                "provenance": provenance(),
                "reference_date_used_in_experiments": AS_OF.isoformat(),
            },
            fh,
            indent=1,
            default=float,
        )
    emb.save()
    print(meta, f"-> {path} ({path.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
