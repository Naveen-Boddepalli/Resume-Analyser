# EviMatch: evidence-grounded, bias-audited resume screening

EviMatch scores a resume against a job description and **shows the evidence**: for every job
requirement, the resume sentence that supports it; for every score, which signals moved it. Names and
other identity cues are removed before scoring, and a counterfactual bias check reports how much the
score still moves when only an irrelevant cue changes.

It is **decision support**. A person must review the evidence before any hiring outcome.

> The project began as an LLM-prompt demo. It was rebuilt as a research system with a reproducible
> evaluation and a paper (`paper/`). Earlier student-placement prediction code and data were removed.

## What is measured (all numbers come from `research/results/*.json`)

Benchmark: `cnamuangtoun/resume-job-description-fit` (8,000 resume-JD pairs, labels No / Potential / Good Fit).

| Finding | Evidence |
|---|---|
| The official split leaks resumes: 99.9% of test resumes also occur in training. A *resume-identity prior alone* reaches macro-F1 0.42. | `label_noise.json`, `main_S1.json` |
| On a doubly-disjoint split, EviMatch (linear) reaches macro-F1 0.47 versus 0.41 for TF-IDF, BM25, MiniLM, BGE and a supervised embedding head (differences 0.06-0.07, CIs exclude 0). | `main_S2.json` |
| The gain comes from interpretable relational features (skill coverage, experience/education gap); the semantic-embedding group adds no significant accuracy. | `ablation_S2.json` |
| Cited evidence is faithful in a deletion test: removing cited sentences lowers the score about four times more than removing the same amount of random text. | `fidelity.json` |
| Labels are noisy: JD identity explains about 27% of label variance, and 6 of 7 duplicated pairs carry conflicting labels. | `label_noise.json` |

What is **not** measured: the LLM-only baseline and the LLM bias audit (the configured API key had no
request quota; the harness `research/run_llm.py` is ready), human evaluation of explanations, and any
non-English or non-technical-domain validity. See the paper's *Limitations*.

## Quick start

### Docker

```bash
docker-compose up --build        # frontend :3000, backend :8000
```

### Backend (FastAPI, Python 3.12)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # optional: API_KEY, CORS_ORIGINS
uvicorn main:app --reload --port 8000
```

The first request downloads the `all-MiniLM-L6-v2` encoder (about 90 MB). Set
`EVIMATCH_EMBEDDER=hashing` for an offline, non-semantic stand-in (demos and tests only).

### Frontend (Next.js)

```bash
cd frontend && npm ci
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/analyze` | One resume (PDF/DOCX/TXT) + job description -> score, decision band, per-requirement evidence, skills, drivers, redaction report |
| `POST` | `/rank` | Up to 25 resumes against one job description, ranked |
| `POST` | `/audit` | Counterfactual bias check for one resume (name groups, affinity organisations, hobbies, career break) |
| `GET` | `/model` | Model card: features, intended use, limitations |
| `GET` | `/health` | Liveness |

Resumes are parsed in memory and never written to disk or a database. If `API_KEY` is set, requests
must send it in `X-API-Key`; do not expose a key in a public frontend bundle, put a gateway in front instead.

## Repository layout

```
backend/resumatch/   core package: redaction, JD parsing, skills, features, model, fairness audit
backend/             FastAPI service, tests (pytest)
frontend/            Next.js report UI
research/            experiment scripts, results JSON, report builder
paper/               IEEE-format manuscript, bibliography, generated figures and tables
docs/research/       literature review, evaluation protocol and deviation log
```

## Reproducing the experiments

```bash
pip install -r backend/requirements.txt pandas matplotlib      # plus data, see data/README.md
python -I research/run_main.py S1        # official split
python -I research/run_main.py S2        # doubly-disjoint, 5 folds
python -I research/run_ablation.py S2
python -I research/run_fidelity.py
python -I research/run_learning_curve.py
python -I research/run_bias_audit.py
python -I research/make_report.py        # figures + LaTeX tables
```

Scripts verify dataset checksums, fix seeds (13) and write library versions and the git commit into each
result file. `docs/research/PROTOCOL.md` lists every deviation from the pre-specified protocol.

## Responsible use

* Employment screening is a regulated, high-risk use of AI in several jurisdictions (for example the EU
  AI Act). This repository is research software, not a compliance product.
* Redaction removes *explicit* identifiers only. Proxy signals remain and are quantified by `/audit`.
* Validate on your own data, keep a human in the loop, and log decisions.

## Development

```bash
black backend research && flake8 backend research && mypy backend --ignore-missing-imports
pytest backend
cd frontend && npm run lint && npm run build
```

## License

MIT, see [LICENSE](LICENSE). The benchmark dataset has no stated licence; it is not redistributed here.
