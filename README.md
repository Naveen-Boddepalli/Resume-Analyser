# 🚀 AI Placement Readiness Platform

![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![CatBoost](https://img.shields.io/badge/CatBoost-ML-yellow)
![Supabase](https://img.shields.io/badge/Supabase-DB-3ECF8E?logo=supabase)
![Mistral](https://img.shields.io/badge/Mistral-LLM-f55036)

> **🔗 [Live Demo: Try the Resume Analyser Here!](https://resume-analyser-pink-rho.vercel.app/)**

The **AI Placement Readiness Platform** is an intelligent, end-to-end tool designed to analyze student resumes and predict their campus placement outcomes. By combining Machine Learning (CatBoost), Natural Language Processing (spaCy, PyMuPDF), and Large Language Models (Mistral), the platform provides students with highly actionable insights to improve their career prospects.

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
- **Styling**: Tailwind CSS
- **Components**: `shadcn/ui`

### Backend
- **Framework**: FastAPI (Python)
- **Task Queue**: Built-in `BackgroundTasks` for asynchronous ML processing
- **Database & Storage**: Supabase (PostgreSQL + Object Storage)

### Machine Learning & NLP
- **Predictive Modeling**: CatBoost, XGBoost
- **Explainability**: SHAP (SHapley Additive exPlanations)
- **Document Parsing**: `PyMuPDF` (fitz), `python-docx`
- **NLP**: `spaCy`

### AI / LLM
- **Inference**: Mistral API (High-speed structured generation)

---

## 🚀 Getting Started

Follow these instructions to set up the project locally.

> [!IMPORTANT]
> Ensure you have Python 3.10+ and Node.js 20+ installed on your system before proceeding.

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
   pip install black flake8 mypy pytest httpx
   ```

3. Configure Environment Variables:
   Create a `.env` file in the `backend/` directory:
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
   *The backend API will be available at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.*

### 2. Frontend Setup (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure Environment Variables:
   Create a `.env.local` file in the `frontend/` directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Run the development server:
   ```bash
   npm run dev
   ```
   *The frontend will be available at `http://localhost:3000`.*

---

## 🧪 Pre-Push Testing & CI Guidelines

To maintain a robust and bug-free codebase, we employ strict Continuous Integration (CI) pipelines using GitHub Actions. **Code that fails these checks will be blocked from deployment.** 

Before pushing your commits or opening a Pull Request, please ensure you run the following checks locally:

> [!TIP]
> For more detailed contribution guidelines, please refer to our [CONTRIBUTING.md](CONTRIBUTING.md).

### Backend Checks
Run these commands inside the `backend/` directory with your virtual environment activated:

1. **Formatting**: Ensure your code meets style standards.
   ```bash
   black .
   ```
2. **Linting**: Check for syntax errors and unused variables.
   ```bash
   flake8 .
   ```
3. **Type Checking**: Verify Python static typing.
   ```bash
   mypy . --ignore-missing-imports
   ```
4. **Unit Tests**: Run the test suite to ensure no endpoints are broken.
   ```bash
   pytest
   ```

### Frontend Checks
Run these commands inside the `frontend/` directory:

1. **Linting**: Run the Next.js ESLint configuration.
   ```bash
   npm run lint
   ```
2. **Type Check & Build**: Ensure the application compiles fully without errors.
   ```bash
   npm run build
   ```

---

## 📡 API Endpoints (Backend)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Uploads a resume (PDF/DOCX), saves to Supabase, and enqueues the analysis task. Returns a `job_id`. |
| `GET`  | `/result/{job_id}` | Checks the status of an analysis job (`pending`, `processing`, `completed`, `failed`). |
| `GET`  | `/report/{job_id}` | Retrieves the full structured JSON report (probabilities, salary range, SHAP, recommendations). |
| `POST` | `/demo` | Runs an instant analysis on a sample resume payload. |
| `GET`  | `/salary-distribution` | Returns historical placement salary percentiles from the ML training dataset. |

---

## 🗺️ Roadmap & Future Enhancements

The current V1 represents a complete MVP. Planned future (V2) enhancements include:
- **Advanced Orchestration**: Celery & Redis for handling high-concurrency workloads.
- **Enhanced NLP**: Sentence Transformers and FAISS for semantic skill matching.
- **Model Tracking**: MLflow for versioning models and tracking experiment metrics.
- **User Accounts**: Advanced authentication (beyond JWT) for users to track their progress over time.
- **Exporting**: Downloadable PDF reports of the generated insights.

---

## 📄 License

This project is licensed under the MIT License.
