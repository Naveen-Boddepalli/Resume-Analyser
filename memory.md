# Project Memory

This file is a persistent memory store for the **AI-based Resume Screening and Job-Matching System** project.

## Project Overview
The platform acts as a screening tool for recruiters. It analyzes a candidate's resume against a specific Job Description (JD) using an LLM to evaluate the match score, identify matching and missing skills, and provide a shortlisting recommendation.

## Important Paths
- **`/backend/`**: FastAPI server, handles API endpoints, background tasks, resume parsing, and LLM matching.
- **`/frontend/`**: Next.js (App Router) web application, built with Tailwind CSS and `shadcn/ui`, featuring a recruiter dashboard.
- **`/data/`**: Datasets (previously used for EDA and training).

## Tech Stack & Architecture Details
- **Frontend**: Next.js, Tailwind CSS, shadcn/ui. (Port: 3000)
- **Backend**: FastAPI with built-in `BackgroundTasks`. (Port: 8000)
- **Database/Storage**: Supabase (PostgreSQL + Object Storage).
- **NLP/Parsing**: `PyMuPDF` (fitz) for PDF, `python-docx` for DOCX.
- **AI/LLM**: Mistral (via API) for semantic matching between Resume and Job Description.

## Current State
- The project has pivoted from predicting student placement outcomes to an AI Resume Screening and Job-Matching tool for recruiters.
- **Backend**: Replaced CatBoost ML models with an LLM prompt that takes a parsed resume and a JD, returning a JSON response with Match Score, Decision, and Skill Analysis.
- **Frontend**: Redesigned dashboard to display "Match Score", "Screening Decision", "Matching Skills", "Missing Skills", and a "Recruiter Summary". Removed student-focused tools like What-If Sliders and Sensitivity Analysis.
- Configured agent to read and write to this file continuously for context preservation.
- Automated CI/CD pipelines (GitHub Actions) remain in place for backend/frontend checks and Docker publishing.

## Important Notes & Decisions
- The matching logic relies entirely on the LLM (Mistral API) to compare extracted features from the resume against the raw Job Description text.
- Fallback JSON responses are used if the LLM rate-limits or fails.
- The UI accepts the JD as a copy-pasted text string via a textarea to simplify the MVP.
