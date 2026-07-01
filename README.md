# 🚀 AI Placement Readiness Platform

![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![CatBoost](https://img.shields.io/badge/CatBoost-ML-yellow)
![Supabase](https://img.shields.io/badge/Supabase-DB-3ECF8E?logo=supabase)
![Mistral](https://img.shields.io/badge/Mistral-LLM-f55036)

[![Backend CI/CD](https://github.com/Naveen-Boddepalli/Resume-Analyser/actions/workflows/backend-ci-cd.yml/badge.svg)](https://github.com/Naveen-Boddepalli/Resume-Analyser/actions/workflows/backend-ci-cd.yml)
[![Frontend CI](https://github.com/Naveen-Boddepalli/Resume-Analyser/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/Naveen-Boddepalli/Resume-Analyser/actions/workflows/frontend-ci.yml)
[![Security Checks](https://github.com/Naveen-Boddepalli/Resume-Analyser/actions/workflows/security-ci.yml/badge.svg)](https://github.com/Naveen-Boddepalli/Resume-Analyser/actions/workflows/security-ci.yml)

> **🔗 [Live Demo: Try the Resume Analyser Here!](https://resume-analyser-pink-rho.vercel.app/)**

The **AI Placement Readiness Platform** is an intelligent, end-to-end tool designed to analyze student resumes and predict their campus placement outcomes. By combining Machine Learning, Natural Language Processing, and Large Language Models, the platform provides students with highly actionable insights to improve their career prospects.

---

## 📑 Table of Contents

- [✨ Key Features](#-key-features)
- [🛠️ Tech Stack](#-tech-stack)
- [🚀 Getting Started](#-getting-started)
  - [🐳 Run with Docker (Easiest Way)](#-run-with-docker-easiest-way)
  - [1. Backend Setup (FastAPI)](#1-backend-setup-fastapi)
  - [2. Frontend Setup (Next.js)](#2-frontend-setup-nextjs)
- [🧪 CI/CD & Testing Guidelines](#-cicd--testing-guidelines)
- [📡 API Endpoints](#-api-endpoints)
- [🤝 Contributing](#-contributing)
- [🗺️ Roadmap](#-roadmap)
- [📄 License](#-license)

---

## ✨ Key Features

- **Resume Parsing Engine**: Robustly extracts key information (CGPA, skills, projects, internships) from PDF and DOCX resumes.
- **Placement Probability Model**: Uses advanced gradient boosting (CatBoost/XGBoost) to classify placement success chances based on extracted features.
- **Salary Range Predictor**: Employs Quantile Regression to forecast a realistic salary bracket (e.g., 7.8 – 10.2 LPA) rather than a single point estimate.
- **Explainable AI (SHAP)**: Breaks down the ML prediction into human-readable *strengths* (positive contributors) and *weaknesses* (negative contributors).
- **LLM-Powered Recommendations**: Generates highly tailored, specific, and actionable advice to improve placement odds using Mistral's high-speed inference.
- **Modern Dashboard**: A sleek, responsive Next.js frontend built with Tailwind CSS and `shadcn/ui` for an intuitive user experience.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js (App Router)
- **Styling**: Tailwind CSS, `shadcn/ui`

### Backend
- **Framework**: FastAPI (Python)
- **Task Queue**: Built-in `BackgroundTasks` for asynchronous ML processing
- **Database & Storage**: Supabase (PostgreSQL + Object Storage)

### Machine Learning & NLP
- **Predictive Modeling**: CatBoost, XGBoost
- **Explainability**: SHAP (SHapley Additive exPlanations)
- **Document Parsing & NLP**: `PyMuPDF` (fitz), `python-docx`, `spaCy`

### AI / LLM
- **Inference**: Mistral API (High-speed structured generation)

---

## 🚀 Getting Started

Ensure you have **Python 3.10+** and **Node.js 20+** installed on your system before proceeding with manual setup, or just Docker for the containerized setup.

### 🐳 Run with Docker (Easiest Way)

You can run the entire application (frontend + backend) using a single command with Docker.

1. Create a `.env` file in the `backend/` directory:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   MISTRAL_API_KEY=your_mistral_api_key
   MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
   ```
2. From the root directory of the project, run:
   ```bash
   docker-compose up --build
   ```
   *Your frontend will be available at `http://localhost:3000` and the backend at `http://localhost:8000`.*

### 1. Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   
   # Install development and testing tools
   pip install "black[jupyter]" flake8 mypy pytest httpx bandit
   ```
3. Configure Environment Variables in `backend/.env`:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   MISTRAL_API_KEY=your_mistral_api_key
   MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
   ```
4. Run the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *API documentation is available at `http://localhost:8000/docs`.*

### 2. Frontend Setup (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm ci
   ```
3. Configure Environment Variables in `frontend/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```

---

## 🧪 CI/CD & Testing Guidelines

To maintain a robust and secure codebase, this repository enforces strict Continuous Integration (CI) pipelines using GitHub Actions. **Code that fails these checks will be blocked from merging.**

Before pushing your commits or opening a Pull Request, please ensure your code passes the following local checks:

### Backend & ML Checks
Run these from the root of the project with your virtual environment activated:
- **Formatting**: `black backend ml`
- **Linting**: `flake8 backend ml`
- **Type Checking**: `mypy backend ml --ignore-missing-imports`
- **Security Audit**: `bandit -r backend ml -ll -i`
- **Unit Tests**: `pytest backend`

### Frontend Checks
Run these inside the `frontend/` directory:
- **Linting**: `npm run lint`
- **Security Audit**: `npm audit --audit-level=high`
- **Build Verification**: `npm run build`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Uploads a resume (PDF/DOCX), saves to Supabase, and enqueues the analysis task. Returns a `job_id`. |
| `GET`  | `/result/{job_id}` | Checks the status of an analysis job (`pending`, `processing`, `completed`, `failed`). |
| `GET`  | `/report/{job_id}` | Retrieves the full structured JSON report (probabilities, salary range, SHAP, recommendations). |
| `POST` | `/demo` | Runs an instant analysis on a sample resume payload. |
| `GET`  | `/salary-distribution` | Returns historical placement salary percentiles from the ML training dataset. |

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest enhancements.

---

## 🗺️ Roadmap

Planned future (V2) enhancements include:
- **Advanced Orchestration**: Celery & Redis for handling high-concurrency workloads.
- **Enhanced NLP**: Sentence Transformers and FAISS for semantic skill matching.
- **Model Tracking**: MLflow for versioning models and tracking experiment metrics.
- **User Accounts**: Advanced authentication (beyond JWT) for users to track their progress over time.
- **Exporting**: Downloadable PDF reports of the generated insights.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
