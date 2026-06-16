---

## AI Placement Readiness Platform — MVP Plan

---

### Dataset

Use the **Kaggle Campus Recruitment / Engineering Placement dataset** (pin the URL in your repo before writing a single line of code). Before anything else, confirm these columns exist: `cgpa`, `internships_count`, `projects_count`, `coding_skill_score`, `communication_skill_score`, `leadership_score`, `placement_status`, `salary_package_lpa`. Your entire feature mapping layer depends on these names. If the column names differ, fix your mapping layer plan first.

---

### Tech Stack

**Frontend** — Next.js, Tailwind, shadcn/ui

**Backend** — FastAPI with `BackgroundTasks` (no Celery/Redis for MVP — FastAPI's built-in background task runner is enough for one-user-at-a-time MVP usage)

**ML** — CatBoost, XGBoost, SHAP

**NLP** — spaCy, PyMuPDF, python-docx

**LLM** — Groq via API (one structured call per resume)

**Database** — PostgreSQL (Supabase) with Supabase Storage for resume files

**Deployment** — Vercel (Next.js), Render (FastAPI), Supabase (DB + Storage)

Drop for MVP: Celery, Redis, MLflow, Sentence Transformers, FAISS, assessment module.

---

### Phase 0 — Dataset Validation (Day 1–2, not a full week)

Don't spend a week on EDA. Do this in one notebook session:

- Confirm column names match your feature map
- Check class balance: `placement_status.value_counts()`
- Check nulls in key columns
- Run one quick XGBoost and print `feature_importances_` — this tells you which features actually matter before you write any parsing logic
- Check salary column distribution (log-normal? outliers?)

Output: a single `eda.ipynb` committed to the repo. Move on.

---

### Phase 1 — Train Both Models (Week 1)

**Model 1 — Placement classifier**

Target: `placement_status` (0/1)

Train: LogisticRegression, RandomForest, CatBoost. Pick the winner by F1 score on a held-out split. Expected winner: CatBoost.

Save: `placement_model.pkl` + threshold calibration (use `predict_proba`, not just `predict`)

**Model 2 — Salary regressor**

Target: `salary_package_lpa`

Train on placed candidates only (filter `placement_status == 1` first).

Instead of a single point estimate, train two `CatBoostRegressor` models with `loss_function='Quantile:alpha=0.25'` and `loss_function='Quantile:alpha=0.75'`. This gives you a natural salary range (e.g. "7.8 – 10.2 LPA") with almost no extra work. Far more credible than a single number.

Save: `salary_low_model.pkl`, `salary_high_model.pkl`

---

### Phase 2 — Resume Parser (Weeks 2–3, two weeks, not one)

This is where most projects underestimate. Two weeks is realistic.

**Week 2 — extraction**

- PDF: PyMuPDF (`fitz`). Use `page.get_text("blocks")` not `get_text("text")` — preserves layout structure better.
- DOCX: `python-docx`. Same extraction logic, different input format.
- Extract: name, email, CGPA (regex: `8\.7|8\.2` etc.), projects (count `<h3>` or numbered sections), internships (keyword match), certifications (count), skills list.

**Week 3 — robustness**

Test on 10 real resumes from your batch and peers. They will break your parser. Fix the top 3 failure modes. Don't try to fix everything — just make it work on 80% of clean single-column resumes and document the limitation clearly.

Output: a `parser.py` module with a single function `parse_resume(file_path) -> dict` that returns structured JSON.

---

### Phase 3 — Feature Mapping Layer (Week 4)

Your parsed resume gives you: `cgpa`, `projects_count`, `internships_count`, `certifications_count`, `skills_list`.

Your model expects: `coding_skill_score`, `communication_skill_score`, `leadership_score`.

**Estimation rules (keep it simple and explicit):**

```python
def estimate_coding_score(skills, projects_count):
    score = 40  # base
    tech_keywords = ['python', 'java', 'c++', 'react', 'node', 
                     'sql', 'ml', 'deep learning', 'docker']
    score += sum(8 for kw in tech_keywords if kw in skills)
    score += min(projects_count * 5, 20)
    return min(score, 100)

def estimate_communication_score(resume_text):
    score = 50  # base
    leadership_kws = ['led', 'coordinated', 'presented', 'team lead']
    score += sum(5 for kw in leadership_kws if kw in resume_text.lower())
    return min(score, 100)

def estimate_leadership_score(resume_text):
    score = 40
    kws = ['president', 'head', 'lead', 'founder', 'organized', 'mentored']
    score += sum(8 for kw in kws if kw in resume_text.lower())
    return min(score, 100)
```

These are intentionally simple. They are not perfect — document that clearly in the UI ("estimated from resume content"). Perfect is the enemy of shipped.

---

### Phase 4 — SHAP Explainability (Week 5)

```python
import shap
explainer = shap.TreeExplainer(placement_model)
shap_values = explainer.shap_values(feature_vector)
```

From this you get per-feature contribution. Map the top positive and negative contributors back to human-readable labels:

```python
feature_labels = {
    'cgpa': 'Academic score',
    'internships_count': 'Internship experience',
    'coding_skill_score': 'Technical skills',
    ...
}
```

Output a `strengths` list (top 3 positive SHAP values) and `weaknesses` list (top 3 negative SHAP values). This is what populates the dashboard cards.

---

### Phase 5 — LLM Recommendation Engine (Week 6)

One single API call. No streaming, no conversation history, no complexity.

```python
prompt = f"""
A student has the following placement profile:
- Placement probability: {placement_prob}%
- CGPA: {cgpa}
- Projects: {projects_count}
- Internships: {internships_count}
- Key weaknesses: {weaknesses}

Give exactly 4 specific, actionable recommendations to improve placement chances.
Respond only in JSON: {{"recommendations": ["...", "...", "...", "..."]}}
"""
```

Use Groq via API. Parse the JSON response. If parsing fails, fall back to a hardcoded set of generic recommendations — don't let an LLM failure break the whole result page.

---

---

### Phase 6 — FastAPI Backend (Week 7)

Four endpoints only:

```
POST /upload          → saves file to Supabase Storage, enqueues background task
GET  /result/{job_id} → returns status: pending | done | failed
GET  /report/{job_id} → returns full JSON result
POST /demo            → runs analysis on a hardcoded sample resume (no upload)
```

The `BackgroundTasks` handler runs the full pipeline: parse → feature map → predict → SHAP → LLM → save to DB.

Add a `predictions` table with columns: `job_id`, `placement_prob`, `salary_low`, `salary_high`, `shap_values` (jsonb), `recommendations` (jsonb), `strengths` (jsonb), `weaknesses` (jsonb), `created_at`.

---

### Phase 7 — Frontend Dashboard (Week 7, parallel with backend)

Build these four components, nothing else for MVP:

**Upload card** — drag-and-drop PDF/DOCX, submit button, loading state with step text ("Parsing resume… Running analysis… Generating recommendations…")

**Summary row** — stat cards: Placement Probability and Salary Range

**SHAP panel** — simple horizontal bar chart (use recharts or just CSS bars) showing strengths in green, weaknesses in red. No need for a full SHAP waterfall plot.

**Recommendations panel** — numbered list of 4 LLM recommendations

Add the `/demo` endpoint to the landing page so judges/viewers can see results without uploading anything.

---

### Phase 8 — Deployment (Week 8)

- FastAPI → Render (free tier, set `--workers 1` to stay within RAM)
- Next.js → Vercel
- PostgreSQL + Storage → Supabase (free tier)
- Add a `.env.example` file and a `README.md` with a demo GIF

---

### Revised Timeline

| Week | Focus |
|---|---|
| 1 | EDA (2 days) + train both models |
| 2 | Resume parser — extraction |
| 3 | Resume parser — robustness testing |
| 4 | Feature mapping layer |
| 5 | SHAP integration |
| 6 | LLM recommendations |
| 7 | FastAPI endpoints + Next.js dashboard |
| 8 | Deployment + demo mode + README |

---

### Additional features that can be added in this version, after completion of the present plan.

Celery, Redis, MLflow, FAISS, Sentence Transformers, assessment module, what-if sliders, PDF export, user authentication beyond basic JWT. All valid V2 additions — none of them are needed to have a working, impressive MVP.

The deliverable at Week 8 is: upload a resume PDF, get a placement probability, salary range, SHAP breakdown, and 4 recommendations. That's the whole product. Build that cleanly before adding anything else.
