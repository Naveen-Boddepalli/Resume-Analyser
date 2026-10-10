"""Build every figure and LaTeX table of the paper from ``research/results``.

Nothing is typed by hand: if a number appears in the paper it is read from a
JSON file written by an experiment script.

    .venv/bin/python -I research/make_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script dir

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from common import ROOT, auc

RES = ROOT / "research" / "results"
FIG = ROOT / "paper" / "figures"
TAB = ROOT / "paper" / "tables"

# Validated categorical slots (first three pass the all-pairs colour-vision checks) + neutral ink.
BLUE, ORANGE, AQUA, GRAY, INK, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a86", "#0b0b0b", "#d9d8d3"
plt.rcParams.update(
    {
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.edgecolor": GRID,
        "axes.linewidth": 0.8,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "axes.labelcolor": INK,
        "pdf.fonttype": 42,
        "figure.dpi": 150,
    }
)

LABELS = {
    "B0_majority": "B0 majority class",
    "B0r_resume_identity_prior": "B0r resume-identity prior",
    "B1_tfidf": "B1 TF-IDF cosine",
    "B2_bm25": "B2 BM25",
    "B3_minilm_doc": "B3 MiniLM doc. cosine",
    "B4_bge_doc": "B4 BGE doc. cosine",
    "B6_embedding_concat_lr": "B6 embedding head (sup.)",
    "M1_lexical_skills_exp": "M1 lexical+skills+exp.",
    "M2_semantic": "M2 semantic only",
    "M3_evimatch_linear": "M3 EviMatch (linear)",
    "M4_evimatch_gbm": "M4 EviMatch (GBM)",
    "X1_linear_plus_identity_feats": "X1 M3 + identity feats.",
    "X2_gbm_plus_identity_feats": "X2 M4 + identity feats.",
}
ORDER = list(LABELS)


def colour(name: str) -> str:
    if name.startswith(("M", "X")):
        return BLUE
    if name.startswith("B6"):
        return ORANGE
    return GRAY


def load(name: str) -> dict:
    with open(RES / name) as fh:
        return json.load(fh)


def f3(x: float) -> str:
    return f"{x:.3f}"


def clean(ax) -> None:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def fig_macro_f1(s1: dict, s2: dict) -> None:
    names = [n for n in ORDER if n in s1["systems"] or n in s2["systems"]]
    names = [n for n in names if not n.startswith("X")]
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.9), sharey=True)
    for ax, res, title in zip(axes, (s1, s2), ("S1: official split (JD-disjoint)", "S2: doubly disjoint (5 folds)")):
        for i, n in enumerate(names):
            if n not in res["systems"]:
                continue
            p, lo, hi = res["systems"][n]["macro_f1_ci"]
            ax.plot([lo, hi], [i, i], color=colour(n), lw=1.4, solid_capstyle="round")
            ax.plot(p, i, "o", color=colour(n), ms=4.5, mec="white", mew=0.8)
            ax.text(hi + 0.008, i, f3(p), va="center", fontsize=6.5)
        ax.set_title(title, loc="left")
        ax.set_xlim(0.15, 0.62)
        ax.set_xlabel("macro-F1 (95% CI, bootstrap over job descriptions)")
        clean(ax)
    axes[0].set_yticks(range(len(names)))
    axes[0].set_yticklabels([LABELS[n] for n in names])
    axes[0].invert_yaxis()
    fig.tight_layout()
    fig.savefig(FIG / "fig_macro_f1.pdf")
    plt.close(fig)


def fig_roc(s2: dict) -> None:
    df = pd.read_csv(RES / "predictions_S2.csv")
    y = df["y"].to_numpy() == 2
    fig, ax = plt.subplots(figsize=(3.4, 3.1))
    spec = [
        ("B1_tfidf", GRAY, ":", "B1 TF-IDF"),
        ("B3_minilm_doc", GRAY, "--", "B3 MiniLM cosine"),
        ("B6_embedding_concat_lr", ORANGE, "-", "B6 embedding head"),
        ("M3_evimatch_linear", BLUE, "-", "M3 EviMatch"),
    ]
    for name, c, ls, lab in spec:
        s = df[f"{name}__score"].to_numpy()
        order = np.argsort(-s, kind="stable")
        tp = np.cumsum(y[order]) / y.sum()
        fp = np.cumsum(~y[order]) / (~y).sum()
        ax.plot(np.r_[0, fp], np.r_[0, tp], color=c, ls=ls, lw=1.5, label=f"{lab} (AUC {auc(y, s):.2f})")
    ax.plot([0, 1], [0, 1], color=GRID, lw=0.8)
    ax.set_xlabel("False-positive rate")
    ax.set_ylabel("True-positive rate")
    ax.set_title("Good Fit vs. rest, S2", loc="left")
    ax.legend(frameon=False, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "fig_roc.pdf")
    plt.close(fig)


def fig_confusion(s2: dict) -> None:
    cm = np.array(s2["systems"]["M3_evimatch_linear"]["confusion"], dtype=float)
    norm = cm / cm.sum(1, keepdims=True)
    fig, ax = plt.subplots(figsize=(3.0, 2.7))
    ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    names = ["No Fit", "Potential", "Good"]
    ax.set_xticks(range(3), names)
    ax.set_yticks(range(3), names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{int(cm[i, j])}\n({norm[i, j]:.0%})", ha="center", va="center", fontsize=7, color="white" if norm[i, j] > 0.55 else INK)
    ax.set_title("M3 on S2 (row-normalised)", loc="left")
    fig.tight_layout()
    fig.savefig(FIG / "fig_confusion.pdf")
    plt.close(fig)


def fig_ablation(ab2: dict) -> None:
    rows = [(k, v) for k, v in ab2["variants"].items() if k != "full"]
    rows.sort(key=lambda kv: kv[1]["delta_macro_f1_vs_full"]["diff"])
    fig, ax = plt.subplots(figsize=(3.4, 3.4))
    for i, (k, v) in enumerate(rows):
        d = v["delta_macro_f1_vs_full"]
        ax.plot([d["lo"], d["hi"]], [i, i], color=BLUE, lw=1.4, solid_capstyle="round")
        ax.plot(d["diff"], i, "o", color=BLUE, ms=4.5, mec="white", mew=0.8)
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks(range(len(rows)), [k.replace("_", " ") for k, _ in rows])
    ax.set_xlabel(r"$\Delta$ macro-F1 vs. full model (95% CI)")
    ax.set_title("Ablation on S2", loc="left")
    clean(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig_ablation.pdf")
    plt.close(fig)


def fig_learning_curve(lc: dict) -> None:
    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    spec = [("M3", BLUE, "-", "M3 EviMatch"), ("B6", ORANGE, "-", "B6 embedding head"), ("B3_threshold", GRAY, "--", "B3 thresholds")]
    for key, c, ls, lab in spec:
        xs, ms, sd = [], [], []
        for f in lc["fractions"]:
            e = lc["macro_f1"][key][str(f)]
            xs.append(lc["mean_train_pairs"][str(f)])
            ms.append(e["mean"])
            sd.append(e["sd"])
        xs, ms, sd = map(np.array, (xs, ms, sd))
        ax.plot(xs, ms, color=c, ls=ls, lw=1.6, marker="o", ms=3.5, label=lab)
        ax.fill_between(xs, ms - sd, ms + sd, color=c, alpha=0.12, lw=0)
    ax.set_xscale("log")
    ax.set_xlabel("training pairs (log scale)")
    ax.set_ylabel("macro-F1 on S2 test folds")
    ax.legend(frameon=False, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.5)
    fig.tight_layout()
    fig.savefig(FIG / "fig_learning_curve.pdf")
    plt.close(fig)


def fig_audit(au: dict) -> None:
    keys = [r["condition"] for r in au["redaction_on"]["proxy_rows"]]
    fig, ax = plt.subplots(figsize=(3.4, 2.9))
    for off, (label, c, mk) in enumerate((("redaction on", BLUE, "o"), ("redaction off", ORANGE, "s"))):
        rows = au["redaction_on" if off == 0 else "redaction_off"]["proxy_rows"]
        for i, r in enumerate(rows):
            y = i + (-0.16 if off == 0 else 0.16)
            ax.plot(r["ci95"], [y, y], color=c, lw=1.3, solid_capstyle="round")
            ax.plot(r["mean_delta"], y, mk, color=c, ms=4.2, mec="white", mew=0.7, label=label if i == 0 else None)
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks(range(len(keys)), [k.replace("_", " ").replace(":", ": ") for k in keys])
    ax.invert_yaxis()
    ax.set_xlabel("score change vs. neutral control line (0-100 scale)")
    ax.legend(frameon=False, loc="lower left")
    clean(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig_audit.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- tables
def ci(t: list[float]) -> str:
    return f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"


def table_main(s1: dict, s2: dict) -> str:
    names = [n for n in ORDER if n in s1["systems"] or n in s2["systems"]]
    lines = [
        r"\begin{tabular}{l cccc cccc}",
        r"\toprule",
        r" & \multicolumn{4}{c}{S1 official (1,759 pairs, 71 JDs)} & \multicolumn{4}{c}{S2 doubly disjoint ("
        + f"{s2['n_test_pairs']:,} pairs, {s2['n_test_jds']} JDs)"
        + r"} \\",
        r"\cmidrule(lr){2-5}\cmidrule(lr){6-9}",
        r"System & macro-F1 [95\% CI] & Acc. & AUC$_G$ & nDCG@10 & macro-F1 [95\% CI] & Acc. & AUC$_G$ & nDCG@10 \\",
        r"\midrule",
    ]
    for n in names:
        cells = []
        for res in (s1, s2):
            r = res["systems"].get(n)
            if r is None:
                cells += ["--"] * 4
            else:
                cells += [ci(r["macro_f1_ci"]), f3(r["accuracy"]), f3(r["auc_good_vs_rest"]), f3(r["ndcg10"][0])]
        lines.append(LABELS[n].replace("&", r"\&") + " & " + " & ".join(cells) + r" \\")
        if n in ("B6_embedding_concat_lr", "M4_evimatch_gbm"):
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


def table_per_class(s2: dict) -> str:
    r = s2["systems"]["M3_evimatch_linear"]["per_class"]
    lines = [r"\begin{tabular}{lccc}", r"\toprule", r"Class & Precision & Recall & F1 \\", r"\midrule"]
    for c, v in r.items():
        lines.append(f"{c} & {f3(v['precision'])} & {f3(v['recall'])} & {f3(v['f1'])} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


def table_ablation(a1: dict, a2: dict) -> str:
    lines = [
        r"\begin{tabular}{l rr rr}",
        r"\toprule",
        r" & \multicolumn{2}{c}{S1} & \multicolumn{2}{c}{S2} \\",
        r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
        r"Variant & macro-F1 & $\Delta$ & macro-F1 & $\Delta$ \\",
        r"\midrule",
    ]
    for k in a2["variants"]:
        v1, v2 = a1["variants"][k], a2["variants"][k]
        d1 = v1.get("delta_macro_f1_vs_full", {}).get("diff", 0.0)
        d2 = v2.get("delta_macro_f1_vs_full", {}).get("diff", 0.0)
        lines.append(f"{k.replace('_', ' ')} & {f3(v1['macro_f1'])} & {d1:+.3f} & {f3(v2['macro_f1'])} & {d2:+.3f} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


def table_audit(au: dict) -> str:
    lines = [
        r"\begin{tabular}{l rr rr}",
        r"\toprule",
        r" & \multicolumn{2}{c}{Redaction on} & \multicolumn{2}{c}{Redaction off} \\",
        r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
        r"Cue vs. control line & $\Delta$ score & flips & $\Delta$ score & flips \\",
        r"\midrule",
    ]
    on, off = au["redaction_on"]["proxy_rows"], au["redaction_off"]["proxy_rows"]
    for a, b in zip(on, off):
        name = a["condition"].replace("_", " ")
        lines.append(
            f"{name} & {a['mean_delta']:+.2f} [{a['ci95'][0]:+.2f}, {a['ci95'][1]:+.2f}] & {a['decision_flip_rate']:.1%} & "
            f"{b['mean_delta']:+.2f} [{b['ci95'][0]:+.2f}, {b['ci95'][1]:+.2f}] & {b['decision_flip_rate']:.1%} " + r"\\"
        )
    lines.append(r"\midrule")
    lines.append(
        f"max name-cell gap (score pts) & \\multicolumn{{2}}{{c}}{{{au['redaction_on']['name_gap']['max_pairwise_gap']:.3f}}} & "
        f"\\multicolumn{{2}}{{c}}{{{au['redaction_off']['name_gap']['max_pairwise_gap']:.3f}}} " + r"\\"
    )
    lines.append(
        f"max per-pair name variation & \\multicolumn{{2}}{{c}}{{{au['redaction_on']['max_abs_name_variation_per_pair']:.3f}}} & "
        f"\\multicolumn{{2}}{{c}}{{{au['redaction_off']['max_abs_name_variation_per_pair']:.3f}}} " + r"\\"
    )
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    s1, s2 = load("main_S1.json"), load("main_S2.json")
    a1, a2 = load("ablation_S1.json"), load("ablation_S2.json")
    lc, au, fid, noise = load("learning_curve.json"), load("bias_audit_local.json"), load("fidelity.json"), load("label_noise.json")
    fig_macro_f1(s1, s2)
    fig_roc(s2)
    fig_confusion(s2)
    fig_ablation(a2)
    fig_learning_curve(lc)
    fig_audit(au)
    (TAB / "main.tex").write_text(table_main(s1, s2))
    (TAB / "per_class.tex").write_text(table_per_class(s2))
    (TAB / "ablation.tex").write_text(table_ablation(a1, a2))
    (TAB / "audit.tex").write_text(table_audit(au))
    # single JSON of every scalar quoted in the prose, so the text can be checked against it
    facts = {
        "S1_M3": s1["systems"]["M3_evimatch_linear"]["macro_f1"],
        "S2_M3": s2["systems"]["M3_evimatch_linear"]["macro_f1"],
        "fidelity": fid,
        "label_noise": noise,
        "paired_S2": s2["paired_vs_M3"],
        "paired_S1": s1["paired_vs_M3"],
    }
    (TAB / "facts.json").write_text(json.dumps(facts, indent=1, default=float))
    print("figures:", sorted(p.name for p in FIG.glob("*.pdf")))
    print("tables:", sorted(p.name for p in TAB.glob("*")))


if __name__ == "__main__":
    main()
