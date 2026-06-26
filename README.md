# 🚀 AI Placement Readiness Platform

![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)
![CatBoost](https://img.shields.io/badge/CatBoost-ML-yellow)
![Supabase](https://img.shields.io/badge/Supabase-DB-3ECF8E?logo=supabase)
![Mistral](https://img.shields.io/badge/Mistral-LLM-f55036)

**🔗 [Live Demo: Try the Resume Analyser Here!](https://resume-analyser-pink-rho.vercel.app/)**

The **AI Placement Readiness Platform** is an intelligent, end-to-end tool designed to analyze student resumes and predict their campus placement outcomes. By combining Machine Learning (CatBoost), Natural Language Processing (spaCy, PyMuPDF), and Large Language Models (Mistral), the platform provides students with highly actionable insights to improve their career prospects.

---

## ✨ Key Features

- **Resume Parsing Engine**: Robustly extracts key information (CGPA, skills, projects, internships) from PDF and DOCX resumes.
- **Placement Probability Model**: Uses advanced gradient boosting (CatBoost/XGBoost) to classify placement success chances based on extracted features.
- **Salary Range Predictor**: Employs Quantile Regression to forecast a realistic salary bracket (e.g., 7.8 – 10.2 LPA) rather than a single point estimate.
- **Explainable AI (SHAP)**: Breaks down the ML prediction into human-readable *strengths* (positive contributors) and *weaknesses* (negative contributors).
- **LLM-Powered Recommendations**: Generates highly tailored, specific, and actionable advice to improve placement odds using Groq's high-speed inference.
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
- **Inference**: Groq API (High-speed structured generation)

---

## 🚀 Getting Started

Follow these instructions to set up the project locally.

### Prerequisites
- Python 3.9+
- Node.js 18+
- A Supabase account and project
- A Groq API Key

### 1. Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure Environment Variables:
   Create a `.env` file in the `backend/` directory:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   GROQ_API_KEY=your_groq_api_key
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend API will be available at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

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
   The frontend will be available at `http://localhost:3000`.

---

## 📡 API Endpoints (Backend)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Uploads a resume (PDF/DOCX), saves to Supabase, and enqueues the analysis task. Returns a `job_id`. |
| `GET`  | `/result/{job_id}` | Checks the status of an analysis job (`pending`, `done`, `failed`). |
| `GET`  | `/report/{job_id}` | Retrieves the full structured JSON report (probabilities, salary range, SHAP, recommendations). |
| `POST` | `/demo` | Runs an instant analysis on a hardcoded sample resume without requiring an upload. |

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
