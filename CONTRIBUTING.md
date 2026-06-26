# Contributing to AI Placement Readiness Platform

First off, thank you for considering contributing to the AI Placement Readiness Platform! It's people like you that make this tool great. 

This document outlines the process, guidelines, and steps required to contribute to the project, run it locally, and ensure your code is ready to be merged.

---

## 1. Local Development Setup

To contribute to the backend or frontend, you'll need to set up the project locally.

### Prerequisites
- **Python 3.10+**
- **Node.js 20+**
- A **Supabase** account (for local testing of DB/Storage)
- A **Mistral** API Key (for LLM inference)

### Backend Setup (FastAPI)

1. **Clone and navigate** to the backend directory:
   ```bash
   git clone https://github.com/your-username/Resume-Analyser.git
   cd Resume-Analyser/backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   # Install development and testing tools
   pip install black flake8 mypy pytest httpx
   ```

4. **Environment Variables**:
   Create a `.env` file in the `backend/` directory with your local credentials:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   MISTRAL_API_KEY=your_mistral_api_key
   MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
   ```

5. **Run the backend locally**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend API will be available at `http://localhost:8000`. API docs can be found at `http://localhost:8000/docs`.

### Frontend Setup (Next.js)

1. **Navigate** to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Environment Variables**:
   Create a `.env.local` file in the `frontend/` directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run the frontend locally**:
   ```bash
   npm run dev
   ```

---

## 2. Pre-Push Checklist & Tests

Our Continuous Integration (CI) pipeline rigorously checks code quality, formatting, and typing. If these checks fail, your code will **not** be deployed. You must run these checks locally before pushing your code.

### Backend Checks

Make sure your virtual environment is activated, then run the following from the root directory (or `backend/` directory depending on your setup):

1. **Code Formatting (Black)**
   Format your code automatically:
   ```bash
   black backend/
   ```

2. **Linting (Flake8)**
   Check for syntax errors, unused imports, or undefined variables. We ignore some formatting rules (like line length) because `black` handles them, but strict syntax checks remain.
   ```bash
   flake8 backend/
   ```

3. **Type Checking (Mypy)**
   Ensure all Python type hints are correct:
   ```bash
   mypy backend/ --ignore-missing-imports
   ```

4. **Unit Tests (Pytest)**
   Run the test suite to ensure existing features still work:
   ```bash
   pytest backend/
   ```

### Frontend Checks

Run these from the `frontend/` directory:

1. **Linting (ESLint)**
   ```bash
   npm run lint
   ```

2. **Type Checking & Build Verification**
   Ensure the app can compile without errors:
   ```bash
   npm run build
   ```

---

## 3. Pull Request Process

1. **Branch Naming**: 
   Create a new branch for your feature or bugfix (e.g., `feature/add-new-parser` or `bugfix/fix-type-error`).
2. **Commit Messages**: 
   Write clear, concise commit messages. (e.g., `fix: resolve mypy errors in llm.py`).
3. **Run the Checks**: 
   Always run the pre-push checklist defined above!
4. **Submit PR**: 
   Open a pull request against the `main` branch. 
5. **CI Pipeline**: 
   The GitHub Actions CI will automatically run all tests and linters. If it fails, check the logs, fix the issues locally, and push the updates.
6. **Review**: 
   Once CI passes, a maintainer will review your code. After approval, it will be merged and automatically deployed.

---

## 4. Code Style Guidelines

- **Python**: We strictly adhere to `black` formatting and `mypy` static typing. Always include return types and argument types for new functions.
- **Next.js**: We use standard React and Next.js best practices, utilizing Tailwind CSS for styling and `shadcn/ui` for components. Avoid injecting inline styles; use Tailwind utility classes instead.

Thank you for contributing!
