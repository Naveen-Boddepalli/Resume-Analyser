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

All entries below were made **before** any model (other than the TF-IDF diagnostic
in the exploration table) was scored on `test.csv`.

1. *DEV split.* A development split (20% of training JDs, seed 13) was added so the
   pipeline could be debugged without touching `test.csv`. Dev results are not reported.
2. *Identity-like features.* Grouped CV inside the training set gave macro-F1 about 0.51
   while the dev split gave 0.42-0.47. The CV folds share resumes, and resume-only
   attributes (years of experience, education level, skill count) let a model memorise
   resume-level base rates. These seven features are now excluded from the model and
   reported separately (systems X1/X2) to quantify the leak.
3. *Tie-breaking.* Ranking metrics originally broke score ties by file order, which is
   not random in the benchmark (a constant scorer reached nDCG@10 = 0.21). Ties are now
   broken with a seeded random permutation.
4. *Baseline text.* B1-B4 and B6 see raw (un-redacted) text, as typical practice;
   EviMatch systems see redacted text. The cost of redaction is isolated in E3.
5. *LLM baseline (B5) and LLM bias audit not run.* The Mistral key in `backend/.env`
   answers every request with HTTP 429 and `x-ratelimit-limit-req-minute: 0`, i.e. the
   account has no request quota. No workaround (other keys or providers) was attempted.
   The harness (`research/run_llm.py`) is complete and cached, so the experiment can be
   run once quota is restored. All claims about LLM bias in the paper therefore rest on
   cited literature, not on our own measurement.
6. *Redactor defect found by the bias audit, fixed, experiments re-run.* The first audit
   showed up to 1.46 score points of name-dependence with redaction on. Cause: the header
   name pattern allowed whitespace to span a newline, so "Name\nProfessional Summary..."
   was matched as one four-token string and rejected by the section-header stop list,
   leaving the name in place. The same pattern also treated 7 of 643 benchmark resumes that
   begin with a glued header ("SummaryService-oriented ...") as names. Fix: the name must
   sit on one line and may not contain header words, digits or camel-case tokens. Because
   the shipped redactor must equal the evaluated one, E1-E7 and the artefact were re-run
   after the fix; the first-run outputs remain in git history (commit 0ac0238).

