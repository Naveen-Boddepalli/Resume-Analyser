"""E1/E2/E3: main comparison, doubly-disjoint evaluation and ablations.

Usage (from the repository root)::

    .venv/bin/python -I research/run_main.py S1
    .venv/bin/python -I research/run_main.py S2
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script dir

import numpy as np
import pandas as pd
from common import (
    FIGURES,
    SEED,
    auc,
    bootstrap_by_jd,
    brier,
    classification_report,
    doubly_disjoint_folds,
    ece,
    load_data,
    macro_f1,
    paired_bootstrap_diff,
    per_jd_ranking,
    save_json,
)
from modeling import (
    BGE,
    MINILM,
    build_features,
    doc_cosine,
    fit_thresholds,
    make_embedder,
    pair_embeddings,
    select_model,
)
from sklearn.model_selection import GroupKFold

from resumatch import FEATURE_GROUPS, FEATURE_NAMES, FitModel
from resumatch.features import ALL_FEATURES, IDENTITY_FEATURES
from resumatch.model import fit_score
from resumatch.text import STOPWORDS, tokenize


def lexical_baselines(train: pd.DataFrame, df: pd.DataFrame) -> dict[str, np.ndarray]:
    """TF-IDF cosine and BM25 on raw text, statistics fitted on train only."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    tr_r = train.drop_duplicates("rid")["resume_text"].tolist()
    tr_j = train.drop_duplicates("jid")["job_description_text"].tolist()
    vec = TfidfVectorizer(stop_words="english", sublinear_tf=True, min_df=2, max_df=0.9).fit(tr_r + tr_j)
    a = vec.transform(df["resume_text"])
    b = vec.transform(df["job_description_text"])
    tfidf = np.asarray(a.multiply(b).sum(1)).ravel()

    import math

    n = len(tr_r)
    dfc: dict[str, int] = {}
    total = 0
    for t in tr_r:
        toks = tokenize(t)
        total += len(toks)
        for w in set(toks):
            dfc[w] = dfc.get(w, 0) + 1
    idf = {w: math.log((n - c + 0.5) / (c + 0.5) + 1.0) for w, c in dfc.items()}
    avgdl = total / n
    k1, b_ = 1.5, 0.75
    out = np.zeros(len(df))
    for i, (r, j) in enumerate(zip(df["resume_text"], df["job_description_text"])):
        toks = tokenize(r)
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        norm = k1 * (1 - b_ + b_ * len(toks) / avgdl)
        num = den = 0.0
        for w in {t for t in tokenize(j) if t not in STOPWORDS}:
            wi = idf.get(w, 0.0)
            den += wi
            c = tf.get(w, 0)
            if c:
                num += wi * c * (k1 + 1) / (c + norm)
        out[i] = num / den if den else 0.0
    return {"B1_tfidf": tfidf, "B2_bm25": out}


def system_record(name: str, pred: np.ndarray, score: np.ndarray, proba: np.ndarray | None) -> dict:
    return {"name": name, "pred": pred, "score": score, "proba": proba}


def run_fold(
    train: pd.DataFrame, test: pd.DataFrame, emb_mini, emb_mini256, emb_bge256, split: str
) -> tuple[list[dict], dict]:
    y_tr = train["y"].to_numpy()
    g_tr = train["jid"].to_numpy()
    systems: list[dict] = []
    info: dict = {}

    maj = int(np.bincount(y_tr).argmax())
    systems.append(system_record("B0_majority", np.full(len(test), maj), np.zeros(len(test)), None))

    if split in ("S1", "DEV"):
        mean_lab = train.groupby("rid")["y"].mean()
        mode_lab = train.groupby("rid")["y"].agg(lambda s: int(s.value_counts().idxmax()))
        pred = test["rid"].map(mode_lab).fillna(maj).astype(int).to_numpy()
        score = test["rid"].map(mean_lab).fillna(float(y_tr.mean())).to_numpy()
        systems.append(system_record("B0r_resume_identity_prior", pred, score, None))

    # unsupervised similarity baselines with thresholds tuned on train
    lex_tr = lexical_baselines(train, train)
    lex_te = lexical_baselines(train, test)
    sims_tr = dict(lex_tr)
    sims_te = dict(lex_te)
    sims_tr["B3_minilm_doc"], sims_te["B3_minilm_doc"] = doc_cosine(train, emb_mini256), doc_cosine(test, emb_mini256)
    sims_tr["B4_bge_doc"], sims_te["B4_bge_doc"] = doc_cosine(train, emb_bge256), doc_cosine(test, emb_bge256)
    for name in sims_tr:
        t1, t2 = fit_thresholds(sims_tr[name], y_tr)
        systems.append(system_record(name, np.digitize(sims_te[name], [t1, t2]), sims_te[name], None))

    # B6: supervised head on concatenated document embeddings
    E_tr, E_te = pair_embeddings(train, emb_mini256), pair_embeddings(test, emb_mini256)
    best = None
    for C in (0.0003, 0.001, 0.003):
        fs = []
        for a, b in GroupKFold(5).split(E_tr, y_tr, g_tr):
            m = FitModel("logreg", [f"e{i}" for i in range(E_tr.shape[1])], C=C).fit(E_tr[a], y_tr[a])
            fs.append(macro_f1(y_tr[b], m.decide(m.predict_proba(E_tr[b]))))
        if best is None or np.mean(fs) > best[0]:
            best = (float(np.mean(fs)), C)
    assert best is not None
    m6 = FitModel("logreg", [f"e{i}" for i in range(E_tr.shape[1])], C=best[1]).fit(E_tr, y_tr)
    P = m6.predict_proba(E_te)
    systems.append(system_record("B6_embedding_concat_lr", m6.decide(P), fit_score(P), P))
    info["B6_C"] = best[1]

    # EviMatch feature models
    built = build_features(train, {"train": train, "test": test}, emb_mini)
    Xtr, Xte = built.X["train"], built.X["test"]

    def cols(names: list[str]) -> list[int]:
        return [ALL_FEATURES.index(n) for n in names]

    specs = {
        "M1_lexical_skills_exp": (
            FEATURE_GROUPS["lexical"] + FEATURE_GROUPS["skills"] + FEATURE_GROUPS["experience"],
            ("logreg",),
        ),
        "M2_semantic": (FEATURE_GROUPS["semantic"], ("logreg",)),
        "M3_evimatch_linear": (FEATURE_NAMES, ("logreg",)),
        "M4_evimatch_gbm": (FEATURE_NAMES, ("gbm",)),
        "X1_linear_plus_identity_feats": (FEATURE_NAMES + IDENTITY_FEATURES, ("logreg",)),
        "X2_gbm_plus_identity_feats": (FEATURE_NAMES + IDENTITY_FEATURES, ("gbm",)),
    }
    for name, (names, kinds) in specs.items():
        c = cols(names)
        model, rep = select_model(Xtr[:, c], y_tr, g_tr, list(names), kinds=kinds)
        P = model.predict_proba(Xte[:, c])
        systems.append(system_record(name, model.decide(P), fit_score(P), P))
        info[name] = rep["chosen"]
    return systems, {"info": info, "built": built}


def main(split: str) -> None:
    train_df, test_df = load_data()
    emb_mini = make_embedder(MINILM, 128)
    emb_mini256 = make_embedder(MINILM, 256)
    emb_bge256 = make_embedder(BGE, 256)
    t0 = time.time()
    if split == "S1":
        folds = [(train_df, test_df)]
    elif split == "DEV":  # development split carved from train only; never touches test.csv
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
    all_test, per_system, fold_info = [], {}, []
    for k, (tr, te) in enumerate(folds):
        print(f"[{split}] fold {k}: train={len(tr)} test={len(te)} ({time.time() - t0:.0f}s)", flush=True)
        systems, extra = run_fold(tr, te, emb_mini, emb_mini256, emb_bge256, split)
        fold_info.append(extra["info"])
        all_test.append(te.assign(fold=k))
        for s in systems:
            d = per_system.setdefault(s["name"], {"pred": [], "score": [], "proba": []})
            d["pred"].append(s["pred"])
            d["score"].append(s["score"])
            if s["proba"] is not None:
                d["proba"].append(s["proba"])
    test = pd.concat(all_test, ignore_index=True)
    y = test["y"].to_numpy()
    results: dict = {
        "split": split,
        "n_test_pairs": int(len(test)),
        "n_test_jds": int(test["jid"].nunique()),
        "n_test_resumes": int(test["rid"].nunique()),
        "systems": {},
    }
    preds = pd.DataFrame({"rid": test["rid"], "jid": test["jid"], "y": y, "fold": test["fold"]})
    rank_tables = {}
    for name, d in per_system.items():
        pred = np.concatenate(d["pred"])
        score = np.concatenate(d["score"])
        preds[f"{name}__pred"] = pred
        preds[f"{name}__score"] = score
        rep = classification_report(y, pred, score)
        rep["macro_f1_ci"] = bootstrap_by_jd(test, lambda idx, p=pred: macro_f1(y[idx], p[idx]))
        rep["auc_good_ci"] = bootstrap_by_jd(test, lambda idx, s=score: auc(y[idx] == 2, s[idx]))
        rank = per_jd_ranking(test, score)
        rank_tables[name] = rank
        for col in ("ndcg5", "ndcg10", "ap_good"):
            v = rank[col].to_numpy()
            rng = np.random.default_rng(SEED)
            boots = [np.nanmean(v[rng.integers(0, len(v), len(v))]) for _ in range(2000)]
            rep[col] = [float(np.nanmean(v)), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
        rep["n_jds_ranked"] = int(len(rank))
        if d["proba"]:
            P = np.concatenate(d["proba"])
            rep["brier"] = brier(y, P)
            rep["ece_good"] = ece((y == 2).astype(float), P[:, 2])
        results["systems"][name] = rep
    # paired comparisons of the proposed model against each baseline
    ref = "M3_evimatch_linear"
    comps = {}
    for other in per_system:
        if other == ref:
            continue
        pa, pb = np.concatenate(per_system[ref]["pred"]), np.concatenate(per_system[other]["pred"])
        comps[other] = paired_bootstrap_diff(
            test, lambda idx: macro_f1(y[idx], pa[idx]), lambda idx: macro_f1(y[idx], pb[idx]), n_boot=1000
        )
        ja = rank_tables[ref].set_index("jid")["ndcg10"]
        jb = rank_tables[other].set_index("jid")["ndcg10"]
        diff = (ja - jb).dropna().to_numpy()
        rng = np.random.default_rng(SEED)
        boots = np.array([diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(2000)])
        comps[other]["ndcg10_diff"] = {
            "diff": float(diff.mean()),
            "lo": float(np.percentile(boots, 2.5)),
            "hi": float(np.percentile(boots, 97.5)),
        }
    results["paired_vs_M3"] = comps
    results["fold_info"] = fold_info
    results["seconds"] = time.time() - t0
    save_json(f"main_{split}.json", results)
    preds.to_csv(FIGURES.parent / "results" / f"predictions_{split}.csv", index=False)
    print(f"[{split}] done in {time.time() - t0:.0f}s")
    for name, rep in results["systems"].items():
        print(
            f"{name:30s} macroF1 {rep['macro_f1']:.3f} acc {rep['accuracy']:.3f} AUCgood {rep['auc_good_vs_rest']:.3f} nDCG@10 {rep['ndcg10'][0]:.3f}"
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "S1")
