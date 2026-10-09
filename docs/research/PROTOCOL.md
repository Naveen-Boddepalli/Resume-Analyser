# Evaluation protocol (fixed before final test-set evaluation)

Written before the held-out test split was scored with any model other than a
single TF-IDF diagnostic. Deviations, if any, are logged at the bottom of this
file with the reason.

## Data

* `cnamuangtoun/resume-job-description-fit` (Hugging Face Hub). No dataset
  card or licence is published; provenance of the labels is undocumented.
* Official split: 6,241 train / 1,759 test pairs, labels `No Fit`,
  `Potential Fit`, `Good Fit`.
* Raw files live in `data/raw/` (git-ignored). `research/data.py` records the
  SHA-256 of each file and refuses to run if they differ.

### Facts established during exploration (train/test only inspected for counts)

| Property | Train | Test |
|---|---|---|
| Pairs | 6,241 | 1,759 |
| Unique resumes | 642 | 477 |
| Unique job descriptions | 280 | 71 |
| Test resumes also in train | n/a | 99.9% |
| Test JDs also in train | n/a | 0% |
| Majority-class share | 50.4% | 48.7% |
| Duplicate pairs with conflicting labels | 6 of 7 duplicated pairs | n/a |

Consequences: (i) the official split is JD-disjoint but **not**
resume-disjoint; (ii) labels are noisy, so absolute scores will be low for
every method.

## Tasks and metrics

| Id | Task | Metrics |
|---|---|---|
| T1 | 3-class fit classification (maps to Reject / Review / Shortlist) | macro-F1 (primary), accuracy, per-class P/R/F1, confusion matrix, quadratic-weighted kappa |
| T2 | Binary screening: `Good Fit` vs rest and `No Fit` vs rest | ROC-AUC, average precision |
| T3 | Per-JD ranking of candidate resumes (graded relevance 0/1/2) | nDCG@5, nDCG@10, MAP over JDs with >= 5 candidates |
| T4 | Calibration of the fit score | Brier score, expected calibration error |

Uncertainty: 95% percentile bootstrap, **resampling job descriptions** (the
unit of independence), 2,000 resamples, fixed seed. Paired differences
between systems use the same resamples.

## Splits

* **S1 official**: train -> test (JD-disjoint).
* **S2 doubly disjoint**: pool all 8,000 pairs, randomly partition resumes and
  JDs into 5 folds each (seed 13). For fold k, train on pairs whose resume is
  outside R_k and JD outside J_k; test on pairs with resume in R_k and JD in
  J_k. Neither the resume nor the JD of a test pair is ever seen in training.

Hyper-parameters are chosen by 5-fold `GroupKFold` (grouped by JD) **inside
the training portion only**. Where an interpretable linear model is within one
standard error of the best model, the linear model is preferred.

## Systems

| Id | System | Supervised |
|---|---|---|
| B0 | Majority class | yes |
| B0r | Resume-identity prior (diagnostic for leakage, not a competitor) | yes |
| B1 | TF-IDF cosine + tuned thresholds | thresholds only |
| B2 | BM25 (JD as query) + tuned thresholds | thresholds only |
| B3 | MiniLM-L6 document cosine + tuned thresholds | thresholds only |
| B4 | BGE-small document cosine + tuned thresholds | thresholds only |
| B5 | Zero-shot LLM (Mistral `mistral-small-latest`, temperature 0), stratified subset of 300 test pairs | no |
| B6 | Embedding-concatenation head (u, v, u*v, \|u-v\|) + logistic regression | yes |
| M1 | EviMatch-lexical: TF-IDF + BM25 + skill coverage + experience/education | yes |
| M2 | EviMatch-semantic: requirement-level coverage + document cosine | yes |
| M3 | EviMatch (full): M1 + M2, linear head | yes |
| M4 | EviMatch-GBM: same features, gradient-boosted head | yes |

Ablations remove one feature group at a time from M3.

## Experiments

| Id | Question |
|---|---|
| E1 | Classification and ranking quality on S1 |
| E2 | Same on S2 and against the LLM subset (B5) |
| E3 | Ablation of feature groups |
| E4 | Explanation fidelity: delete the sentences cited as evidence vs the same number of random sentences; compare score drop |
| E5 | Learning curve: score vs number of training pairs |
| E6 | Counterfactual bias audit (explicit name cues, gendered-affiliation proxy cues), with and without redaction, for M3 and B5 |
| E7 | Label-noise probe: agreement among duplicate pairs and ceiling analysis |

## Reporting rules

* Every number in the paper is produced by a script under `research/` and
  stored in `research/results/*.json` with the git commit and library versions.
* Negative or null results are reported.
* The test split is evaluated once per final configuration. Any further use
  is logged below.

## Deviation log

(none yet)
