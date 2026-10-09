"""E6 (local part): counterfactual bias audit of EviMatch with and without redaction.

Trains the linear EviMatch model on the official training split, then scores
perturbed copies of a fixed random sample of test pairs.

    .venv/bin/python -I research/run_bias_audit.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script dir

import numpy as np
from common import AS_OF, SEED, load_data, save_json
from modeling import MINILM, build_features, make_embedder, select_model

from resumatch import FEATURE_NAMES
from resumatch.fairness import NAMES, PROXIES, name_gap, permutation_pvalue, summarise, with_line, with_name
from resumatch.features import ALL_FEATURES, analyse_pair, prepare_jobs, prepare_resumes

N_PAIRS = 600


def audit_system(train, sample, embedder, do_redact: bool) -> dict:
    built = build_features(train, {"train": train}, embedder, do_redact=do_redact)
    cols = [ALL_FEATURES.index(n) for n in FEATURE_NAMES]
    model, rep = select_model(
        built.X["train"][:, cols], train["y"].to_numpy(), train["jid"].to_numpy(), list(FEATURE_NAMES), kinds=("logreg",)
    )
    jd_texts = sample["job_description_text"].tolist()
    pj = prepare_jobs(jd_texts, embedder, built.lexicon)
    base_resumes = sample["resume_text"].tolist()

    def score_variant(transform) -> tuple[np.ndarray, np.ndarray]:
        texts = [transform(t, i) for i, t in enumerate(base_resumes)]
        pr = prepare_resumes(texts, embedder, built.lexicon, do_redact=do_redact, as_of=AS_OF)
        X = np.array([[analyse_pair(r, j, built.stats).features[n] for n in FEATURE_NAMES] for r, j in zip(pr, pj)])
        P = model.predict_proba(X)
        return model.score(X), model.decide(P)

    scores: dict[str, np.ndarray] = {}
    decisions: dict[str, np.ndarray] = {}
    scores["original"], decisions["original"] = score_variant(lambda t, i: t)

    # explicit name cues: average over the four names of each cell
    for cell, names in NAMES.items():
        s_acc, d_acc = [], []
        for nm in names:
            s, d = score_variant(lambda t, i, nm=nm: with_name(t, nm))
            s_acc.append(s)
            d_acc.append(d)
        scores[f"names:{cell}"] = np.mean(s_acc, axis=0)
        decisions[f"names:{cell}"] = d_acc[0]

    reference: dict[str, str] = {}
    for family, lines in PROXIES.items():
        ctrl = f"{family}:control"
        scores[ctrl], decisions[ctrl] = score_variant(lambda t, i, ln=lines["control"]: with_line(t, ln))
        for key, line in lines.items():
            if key == "control":
                continue
            name = f"{family}:{key}"
            scores[name], decisions[name] = score_variant(lambda t, i, ln=line: with_line(t, ln))
            reference[name] = ctrl

    groups = sample["jid"].to_numpy()
    rows = summarise(scores, decisions, reference, groups)
    out = {
        "redaction": do_redact,
        "model": rep["chosen"],
        "n_pairs": int(len(sample)),
        "n_jds": int(sample["jid"].nunique()),
        "name_cell_mean_score": {k.split(":", 1)[1]: float(v.mean()) for k, v in scores.items() if k.startswith("names:")},
        "name_gap": name_gap(scores, groups),
        "max_abs_name_variation_per_pair": float(
            np.max(np.ptp(np.stack([v for k, v in scores.items() if k.startswith("names:")]), axis=0))
        ),
        "proxy_rows": [
            {
                "condition": r.condition,
                "reference": r.reference,
                "mean_delta": r.mean_delta,
                "ci95": list(r.ci),
                "decision_flip_rate": r.flip_rate,
                "n": r.n,
            }
            for r in rows
        ],
        "paired_tests": {
            "white_male_vs_black_male_p": permutation_pvalue(scores["names:white_male"], scores["names:black_male"]),
            "white_male_vs_black_female_p": permutation_pvalue(scores["names:white_male"], scores["names:black_female"]),
            "hobbies_female_vs_male_coded_p": permutation_pvalue(scores["hobbies:female_coded"], scores["hobbies:male_coded"]),
        },
        "score_sd_original": float(scores["original"].std()),
    }
    return out


def main() -> None:
    train, test = load_data()
    rng = np.random.default_rng(SEED)
    idx = np.sort(rng.choice(len(test), size=N_PAIRS, replace=False))
    sample = test.iloc[idx].reset_index(drop=True)
    embedder = make_embedder(MINILM, 128)
    t0 = time.time()
    res = {}
    for label, red in (("redaction_on", True), ("redaction_off", False)):
        res[label] = audit_system(train, sample, embedder, red)
        print(f"{label}: done ({time.time() - t0:.0f}s)", flush=True)
        embedder.save()
    save_json("bias_audit_local.json", res)
    for label, r in res.items():
        print(f"\n== {label}  max per-pair name variation = {r['max_abs_name_variation_per_pair']:.4f}")
        print("name gap:", {k: round(v, 3) for k, v in r["name_gap"].items() if k == "max_pairwise_gap" or "black" in k})
        for row in r["proxy_rows"]:
            lo, hi = row["ci95"]
            print(f"  {row['condition']:32s} d={row['mean_delta']:+.3f} [{lo:+.3f},{hi:+.3f}] flips={row['decision_flip_rate']:.3f}")


if __name__ == "__main__":
    main()
