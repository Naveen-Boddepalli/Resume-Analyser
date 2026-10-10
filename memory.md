# Project Memory

## Goal
Publishable, honestly evaluated resume-screening research system (EviMatch) + IEEE-format paper.
Every number in the paper comes from `research/results/*.json` (rebuilt by `research/make_report.py`).

## State (end of session 3)
- DONE & committed: literature review and verified bibliography (`docs/research`, `paper/references.bib`),
  evaluation protocol with deviation log (6 entries), core package `backend/resumatch/`, stateless FastAPI
  (`/analyze /rank /audit /model /health`), Next.js evidence-first UI (lint/tsc/build pass), 23 backend tests,
  mypy/black/flake8 clean, trained artefact, experiments E1-E7 re-run after the redactor fix,
  manuscript `paper/main.tex` -> `paper/main.pdf` (8 pages, 25 references, abstract 237 words),
  legacy placement code/data removed, README/CI/Docker/compose updated, n-gram self-check script.
- REMAINING (needs the user): fill author affiliation and repository URL in `paper/main.tex`;
  pick the target venue and re-flow to its official template/page limit; run an official similarity
  service (iThenticate/Turnitin) if the venue requires it; disclose AI assistance per venue policy.
- REMAINING (engineering/research):
  1. LLM baseline B5 + LLM bias audit: Mistral key in `backend/.env` returns 429 with 0 req/min.
     Harness `research/run_llm.py` is complete (cached, budget-limited); needs quota or a pinned open-weight model.
  2. (resolved in session 3) gendered-organisation audit control now uses the opposite marker; redaction on = exactly 0.
  3. Human evaluation of explanations; second benchmark with documented labels; skill ontology linking.
  4. Pushed to origin/main (https://github.com/Naveen-Boddepalli/Resume-Analyser). All four workflows pass on main
     (checked via badge SVGs). Do NOT poll the unauthenticated GitHub API in a loop: it exhausted the 60/h quota.
     Dependabot reports 36 alerts on the default branch (4 critical): review `frontend/package-lock.json` and
     `backend/requirements.txt` updates. The Render deploy hook fires on push to main; the new backend needs more memory
     (torch + MiniLM) than a 512 MB plan and the live Vercel demo now expects the new API.
  5. Rotate `API_KEY` in backend/.env: it equals the old hard-coded default that sits in git history.

## Key results (see paper Table II/III and research/results)
- Official split leaks: 99.9% of test resumes occur in train; resume-identity prior macro-F1 0.420.
- Doubly-disjoint (S2): similarity baselines 0.405-0.412; EviMatch linear 0.473 [0.437, 0.507]; GBM 0.467;
  supervised embedding head 0.409 (0.480 on S1).
- Ablation (S2): experience -0.053, skills -0.032, lexical 0.000, semantic +0.007 (n.s.); redaction costs 0.000.
- Fidelity: cited-evidence deletion -7.7 pts vs -1.8 random (diff 5.9, CI 5.0-6.9, 86.7% of pairs).
- Audit (600 pairs): names exactly invariant with redaction on; proxy cues -0.03 to -0.22 pts; ~1% flips.
- Labels noisy: JD identity explains 27% of variance; 6 of 7 duplicate pairs conflict.

## Rules
- Do not fabricate results or citations; report null results; the test split is scored once per configuration.
- Disclose AI assistance in the paper; AI-text detectors are unreliable and are not a target.
