# Project Memory

This file is a persistent memory store for the **AI Placement Readiness Platform** (Resume Analyser) project. It will be updated by the AI agent automatically to maintain context across different sessions and tasks.

## Project Overview
The platform analyzes student resumes (PDF/DOCX) and predicts their campus placement outcomes, salary ranges, and provides actionable recommendations using ML, NLP, and LLMs.

## Important Paths
- **`/backend/`**: FastAPI server, handles API endpoints, background tasks, ML inference, and DB interactions.
- **`/frontend/`**: Next.js (App Router) web application, built with Tailwind CSS and `shadcn/ui`.
- **`/ml/`**: Machine learning notebooks and training scripts (CatBoost, XGBoost, SHAP).
- **`/models/`**: Saved model files (e.g., `placement_model.pkl`, `salary_low_model.pkl`).
- **`/data/`**: Datasets (Kaggle Campus Recruitment) used for EDA and training.
- **`/reports/`**: Generated reports or logs.

## Tech Stack & Architecture Details
- **Frontend**: Next.js, Tailwind CSS, shadcn/ui. (Port: 3000)
- **Backend**: FastAPI with built-in `BackgroundTasks`. (Port: 8000)
- **Database/Storage**: Supabase (PostgreSQL + Object Storage).
- **Machine Learning**: CatBoost (primary classifier & quantile regressor), XGBoost.
- **Explainability**: SHAP (SHapley Additive exPlanations) for strengths/weaknesses.
- **NLP/Parsing**: `PyMuPDF` (fitz) for PDF, `python-docx` for DOCX, `spaCy` for text processing.
- **LLM**: Groq API for generating personalized recommendations.

## Current State
- Project is active and currently following the 8-week MVP plan outlined in `PLAN.md`.
- **Live Demo (Frontend)**: https://resume-analyser-pink-rho.vercel.app/
- Configured agent to read and write to this file continuously for context preservation.
- Configured a GitHub Actions workflow (`.github/workflows/backend-ci-cd.yml`) to enforce strict checks (formatting, linting, type-checking, tests) before triggering Render Deploy Hooks.

## Important Notes & Decisions
- MVP uses FastAPI's `BackgroundTasks` instead of Celery/Redis for simplicity.
- The resume parser relies heavily on accurate PDF block extraction (`fitz`) and keyword mapping for feature extraction.
- Salary prediction uses Quantile Regression (alpha=0.25 and 0.75) to provide a realistic range rather than a point estimate.
- The LLM step is a single, structured API call (no conversational history required).
