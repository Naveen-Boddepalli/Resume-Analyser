"""E4: explanation fidelity by deletion.

If the sentences an explanation cites as evidence really drive the score,
removing them must lower the score more than removing the same amount of
random, un-cited text.

    .venv/bin/python -I research/run_fidelity.py
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
from resumatch.features import ALL_FEATURES, COVER_WEAK, analyse_pair, prepare_jobs, prepare_resumes

N_PAIRS = 600
TOP_REQ = 5
TOP_SKILLS = 5
N_RANDOM = 5


def main() -> None:
    train, test = load_data()
    emb = make_embedder(MINILM, 128)
    built = build_features(train, {"train": train}, emb)
    cols = [ALL_FEATURES.index(n) for n in FEATURE_NAMES]
    model, rep = select_model(
        built.X["train"][:, cols],
        train["y"].to_numpy(),
        train["jid"].to_numpy(),
        list(FEATURE_NAMES),
        kinds=("logreg",),
    )
    rng = np.random.default_rng(SEED)
    sample = test.iloc[np.sort(rng.choice(len(test), size=N_PAIRS, replace=False))].reset_index(drop=True)
    pr0 = prepare_resumes(sample["resume_text"].tolist(), emb, built.lexicon, as_of=AS_OF)
    pj = prepare_jobs(sample["job_description_text"].tolist(), emb, built.lexicon)

    def score_text(text: str, j) -> float:
        r = prepare_resumes([text], emb, built.lexicon, do_redact=False, as_of=AS_OF)[0]
        f = analyse_pair(r, j, built.stats).features
        return float(model.score(np.array([[f[n] for n in FEATURE_NAMES]]))[0])

    rows = []
    t0 = time.time()
    for i, (r, j) in enumerate(zip(pr0, pj)):
        a = analyse_pair(r, j, built.stats)
        # cited evidence: best sentence of the strongest matched requirements + skill evidence
        reqs = sorted(
            (m for m in a.matches if m.similarity >= COVER_WEAK),
            key=lambda m: -(m.requirement.weight * m.similarity),
        )[:TOP_REQ]
        cited = {m.sentence_index for m in reqs}
        for _, idx in sorted(a.matched_skills.items())[:TOP_SKILLS]:
            cited.add(idx)
        if not cited or len(cited) >= len(r.sentences):
            continue
        words = sum(len(r.sentences[k].split()) for k in cited)
        full = "\n".join(r.sentences)
        s0 = score_text(full, j)
        s_cited = score_text("\n".join(s for k, s in enumerate(r.sentences) if k not in cited), j)
        others = [k for k in range(len(r.sentences)) if k not in cited]
        drops = []
        for _ in range(N_RANDOM):
            order = rng.permutation(others)
            take, w = set(), 0
            for k in order:
                take.add(int(k))
                w += len(r.sentences[int(k)].split())
                if w >= words:
                    break
            drops.append(s0 - score_text("\n".join(s for k, s in enumerate(r.sentences) if k not in take), j))
        rows.append(
            {
                "jid": sample["jid"][i],
                "n_cited": len(cited),
                "drop_cited": s0 - s_cited,
                "drop_random": float(np.mean(drops)),
            }
        )
        if (i + 1) % 100 == 0:
            print(f"{i + 1}/{N_PAIRS} ({time.time() - t0:.0f}s)", flush=True)
    emb.save()
    import pandas as pd

    df = pd.DataFrame(rows)
    d = (df["drop_cited"] - df["drop_random"]).to_numpy()
    groups = {k: v for k, v in df.groupby("jid").indices.items()}
    keys = list(groups)
    boots = []
    brng = np.random.default_rng(SEED)
    for _ in range(2000):
        pick = brng.integers(0, len(keys), len(keys))
        idx = np.concatenate([groups[keys[p]] for p in pick])
        boots.append(d[idx].mean())
    signs = brng.choice([-1.0, 1.0], size=(5000, len(d)))
    p = float((np.sum(np.abs((signs * d).mean(1)) >= abs(d.mean())) + 1) / 5001)
    out = {
        "n_pairs": int(len(df)),
        "mean_drop_cited": float(df["drop_cited"].mean()),
        "mean_drop_random": float(df["drop_random"].mean()),
        "mean_difference": float(d.mean()),
        "ci95_difference": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
        "cited_larger_share": float((d > 0).mean()),
        "permutation_p": p,
        "mean_sentences_cited": float(df["n_cited"].mean()),
        "model": rep["chosen"],
    }
    save_json("fidelity.json", out)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items() if k != "model"})


if __name__ == "__main__":
    main()
