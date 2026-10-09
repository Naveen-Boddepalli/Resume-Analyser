# Project Memory

## Goal
Turn the resume-screening app into a publishable, honestly evaluated research system (EviMatch):
evidence-grounded resume-JD matching with a blind-screening front end and a counterfactual bias
audit, plus an IEEE-format paper. Every number in the paper must come from `research/results/*.json`.

## State (updated at end of session 1)
- DONE & committed: literature review + verified bibliography (`docs/research`, `paper/references.bib`),
  evaluation protocol with deviation log, core package `backend/resumatch/`, stateless FastAPI
  (`/analyze /rank /audit /model /health`), 20 passing tests, trained artefact, experiments
  E1-E3, E4 (fidelity), E5 (learning curve), E7 (label noise), local bias audit (E6 local).
- Data: `data/raw/resume-job-description-fit/` (git-ignored, SHA-256 checked, no licence/card on the Hub).
- NOT done: (1) frontend still calls removed `/upload` `/result` `/demo` endpoints -> must be rewritten for
  `/analyze` `/rank` `/audit`; (2) paper (IEEEtran .tex + figures + PDF via `tectonic`, installed);
  (3) README/CI/Docker updates (Dockerfile still py3.11 + old requirements; CI py3.10);
  (4) legacy cleanup (models/*.pkl, ml/, reports/, data/student_placement*.csv, test.txt);
  (5) LLM baseline B5 and LLM bias audit: Mistral key returns 429 with 0 req/min, harness `research/run_llm.py` ready;
  (6) figures/tables script from the JSON results; (7) similarity self-check of paper text.

## Key findings so far (see research/results)
- Official split leaks: 99.9% of test resumes occur in train; resume-identity prior alone gets macro-F1 0.42.
- Doubly-disjoint (S2): baselines ~0.41 macro-F1; EviMatch linear 0.473, GBM 0.464; supervised embedding head 0.409.
- Ablation: experience/education relational features matter most; semantic group adds ~nothing; redaction and
  induced vocabulary cost nothing measurable; BGE vs MiniLM no difference.
- Fidelity: deleting cited evidence drops score 7.7 vs 1.8 for length-matched random deletion.
- JD identity explains ~27% of label variance; 6 of 7 duplicate pairs have conflicting labels (noisy labels).
- Bias audit: OPEN ISSUE - with redaction ON the max per-pair score variation across name cells is 1.46 points
  (expected 0 by construction): some names escape `redact()`; investigate before claiming invariance.
  Proxy cues (affinity org, hobbies, career break) shift scores by 0.03-0.22 points, CIs mostly exclude 0.

## Rules
- Do not fabricate results/citations; report null results; test split scored once per configuration.
- Disclose AI assistance in the paper per venue policy; AI-text detectors are unreliable and not a target.
