import os
import uuid
import json
import copy
import joblib
import numpy as np
import pandas as pd
from typing import Optional, Any
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    BackgroundTasks,
    HTTPException,
    Security,
    Request,
    Depends,
)
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from parser import parse_resume
from feature_mapper import (
    estimate_coding_score,
    estimate_communication_score,
    estimate_leadership_score,
)
from explainer import get_shap_values
from llm import generate_recommendations
from config import SUPABASE_URL, SUPABASE_KEY

app = FastAPI(title="AI Placement Readiness Platform API")

API_KEY = os.getenv("API_KEY", "test-secret-key-123")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://resume-analyser-pink-rho.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load Models
models_dir = os.path.join(os.path.dirname(__file__), "../models")
try:
    placement_model = joblib.load(os.path.join(models_dir, "placement_model.pkl"))
    salary_low_model = joblib.load(os.path.join(models_dir, "salary_low_model.pkl"))
    salary_high_model = joblib.load(os.path.join(models_dir, "salary_high_model.pkl"))
except Exception as e:
    print("Warning: Could not load models", e)
    placement_model, salary_low_model, salary_high_model = None, None, None

# Load salary distribution statistics from training data (computed once at startup)
_salary_dist_cache: dict | None = None
try:
    _data_path = os.path.join(
        os.path.dirname(__file__),
        "../data/student_placement_prediction_dataset_2026.csv",
    )
    _train_df = pd.read_csv(_data_path)
    _placed = _train_df[_train_df["placement_status"] == "Placed"]
    _salaries = _placed["salary_package_lpa"].dropna()
    _salary_dist_cache = {
        "placement_rate": round(len(_placed) / len(_train_df) * 100, 1),
        "salary_stats": {
            "p10": round(float(np.percentile(_salaries, 10)), 1),
            "p25": round(float(np.percentile(_salaries, 25)), 1),
            "p50": round(float(np.percentile(_salaries, 50)), 1),
            "p75": round(float(np.percentile(_salaries, 75)), 1),
            "p90": round(float(np.percentile(_salaries, 90)), 1),
            "min": round(float(_salaries.min()), 1),
            "max": round(float(_salaries.max()), 1),
            "mean": round(float(_salaries.mean()), 1),
        },
    }
    del _train_df, _placed, _salaries
except Exception as e:
    print("Warning: Could not load salary distribution data", e)
    _salary_dist_cache = None


def update_job_status(job_id: str, status: str, result: Optional[dict] = None):
    try:
        data: dict[str, Any] = {"status": status}
        if result is not None:
            data["result"] = result
        supabase.table("jobs").update(data).eq("id", job_id).execute()
    except Exception as e:
        print(f"Failed to update job status in Supabase: {e}")


def get_job(job_id: str) -> Optional[dict]:
    try:
        response = supabase.table("jobs").select("*").eq("id", job_id).execute()
        if response.data:
            job = response.data[0]
            return {"status": job["status"], "result": job.get("result")}  # type: ignore
        return None
    except Exception as e:
        print(f"Failed to fetch job from Supabase: {e}")
        return None


def process_resume(job_id: str, file_path: str, storage_path: str):
    try:
        update_job_status(job_id, "processing")

        # 1. Parse resume
        parsed_data = parse_resume(file_path)

        # 2. Map features
        features = {
            "cgpa": parsed_data.get("cgpa", 0.0),
            "projects_count": parsed_data.get("projects_count", 0),
            "internships_count": parsed_data.get("internships_count", 0),
            "certifications_count": parsed_data.get("certifications_count", 0),
            "skills": parsed_data.get("skills_list", []),
            "college_tier": parsed_data.get("college_tier", "Tier 2"),
            "branch": parsed_data.get("branch", "CSE"),
            "coding_score": estimate_coding_score(parsed_data),
            "communication_score": estimate_communication_score(parsed_data),
            "leadership_score": estimate_leadership_score(parsed_data),
        }

        # Format for model
        X_df = pd.DataFrame(
            [
                {
                    "cgpa": features["cgpa"],
                    "internships_count": features["internships_count"],
                    "projects_count": features["projects_count"],
                    "coding_skill_score": features["coding_score"],
                    "communication_skill_score": features["communication_score"],
                    "leadership_score": features["leadership_score"],
                    "college_tier": features["college_tier"],
                    "branch": features["branch"],
                }
            ]
        )

        prob = 0
        salary_low = 0
        salary_high = 0

        if placement_model is not None:
            # get placement probability (class 1)
            prob = int(placement_model.predict_proba(X_df)[0][1] * 100)
            salary_low = round(salary_low_model.predict(X_df)[0], 1)
            salary_high = round(salary_high_model.predict(X_df)[0], 1)

        features["placement_probability"] = prob
        features["salary_low"] = salary_low
        features["salary_high"] = salary_high

        # 3. Explain (SHAP equivalent)
        shap_results = get_shap_values(placement_model, X_df)

        # 4. LLM Recommendations
        recommendations_str = generate_recommendations(features, shap_results)
        try:
            roadmap = json.loads(recommendations_str).get("roadmap", [])
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            roadmap = []

        # Assemble response
        final_result = {
            "features": features,
            "analysis": shap_results,
            "roadmap": roadmap,
        }

        update_job_status(job_id, "completed", final_result)

    except Exception as e:
        update_job_status(job_id, "failed", {"error": str(e)})
    finally:
        # Clean up local file
        if os.path.exists(file_path):
            os.remove(file_path)
        # Optionally, remove from Supabase Storage
        try:
            supabase.storage.from_("resumes").remove([storage_path])
        except Exception as e:
            print(f"Failed to delete {storage_path} from Supabase: {e}")


@app.post("/upload")
@limiter.limit("5/minute")
async def upload_resume(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key),
):
    job_id = str(uuid.uuid4())

    file_path = f"temp_{job_id}_{file.filename}"
    storage_path = f"{job_id}/{file.filename}"

    content = await file.read()

    # 1. Save locally for parser
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    # 2. Upload to Supabase Storage
    try:
        supabase.storage.from_("resumes").upload(
            storage_path, content, file_options={"content-type": file.content_type}  # type: ignore
        )
    except Exception as e:
        print(f"Failed to upload to Supabase storage: {e}")

    # 3. Create job in Supabase database
    try:
        supabase.table("jobs").insert(
            {"id": job_id, "status": "pending", "result": None}
        ).execute()
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500, detail=f"Failed to insert job into DB: {str(e)}"
        )

    background_tasks.add_task(process_resume, job_id, file_path, storage_path)

    return {"job_id": job_id, "status": "pending"}


@app.get("/result/{job_id}")
@limiter.limit("60/minute")
async def get_result(
    request: Request, job_id: str, api_key: str = Depends(get_api_key)
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/report/{job_id}")
@limiter.limit("60/minute")
async def get_report(
    request: Request, job_id: str, api_key: str = Depends(get_api_key)
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        return {"status": job["status"], "message": "Report not ready yet"}

    res = job["result"]
    return {
        "readiness_summary": (
            "Good"
            if res["features"].get("coding_score", 0) > 60
            else "Needs Improvement"
        ),
        "details": res,
    }


class DemoRequest(BaseModel):
    cgpa: float
    projects_count: int
    internships_count: int
    certifications_count: int
    skills_list: list[str]
    college_tier: str
    branch: str
    coding_score: Optional[int] = None
    communication_score: Optional[int] = None
    leadership_score: Optional[int] = None


@app.post("/demo")
@limiter.limit("20/minute")
async def demo_endpoint(
    request: Request, demo_req: DemoRequest, api_key: str = Depends(get_api_key)
):
    features = demo_req.model_dump()

    if features.get("coding_score") is None:
        features["coding_score"] = estimate_coding_score(features)
    if features.get("communication_score") is None:
        features["communication_score"] = estimate_communication_score(features)
    if features.get("leadership_score") is None:
        features["leadership_score"] = estimate_leadership_score(features)

    X_df = pd.DataFrame(
        [
            {
                "cgpa": features["cgpa"],
                "internships_count": features["internships_count"],
                "projects_count": features["projects_count"],
                "coding_skill_score": features["coding_score"],
                "communication_skill_score": features["communication_score"],
                "leadership_score": features["leadership_score"],
                "college_tier": features["college_tier"],
                "branch": features["branch"],
            }
        ]
    )

    prob = 0
    salary_low = 0
    salary_high = 0

    if placement_model is not None:
        prob = int(placement_model.predict_proba(X_df)[0][1] * 100)
        salary_low = round(salary_low_model.predict(X_df)[0], 1)
        salary_high = round(salary_high_model.predict(X_df)[0], 1)

    features["placement_probability"] = prob
    features["salary_low"] = salary_low
    features["salary_high"] = salary_high

    shap_results = get_shap_values(placement_model, X_df)
    recommendations_str = generate_recommendations(features, shap_results)
    try:
        roadmap = json.loads(recommendations_str).get("roadmap", [])
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        roadmap = []

    return {"features": features, "analysis": shap_results, "roadmap": roadmap}


@app.get("/salary-distribution")
@limiter.limit("60/minute")
async def salary_distribution(request: Request, api_key: str = Depends(get_api_key)):
    if _salary_dist_cache is None:
        raise HTTPException(
            status_code=500,
            detail="Salary distribution data not available. Training CSV not found.",
        )
    return _salary_dist_cache


@app.post("/sensitivity")
@limiter.limit("20/minute")
async def sensitivity_analysis(
    request: Request, demo_req: DemoRequest, api_key: str = Depends(get_api_key)
):
    features = demo_req.model_dump()

    if features.get("coding_score") is None:
        features["coding_score"] = estimate_coding_score(features)
    if features.get("communication_score") is None:
        features["communication_score"] = estimate_communication_score(features)
    if features.get("leadership_score") is None:
        features["leadership_score"] = estimate_leadership_score(features)

    def _build_x_df(f: dict) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "cgpa": f["cgpa"],
                    "internships_count": f["internships_count"],
                    "projects_count": f["projects_count"],
                    "coding_skill_score": f["coding_score"],
                    "communication_skill_score": f["communication_score"],
                    "leadership_score": f["leadership_score"],
                    "college_tier": f["college_tier"],
                    "branch": f["branch"],
                }
            ]
        )

    X_base = _build_x_df(features)

    base_prob = 0
    if placement_model is not None:
        base_prob = int(placement_model.predict_proba(X_base)[0][1] * 100)

    # Perturbation definitions: (feature_key, display_name, delta, cap)
    perturbations = [
        ("cgpa", "CGPA", 0.5, 10.0),
        ("internships_count", "Internships", 1, 10),
        ("projects_count", "Projects", 1, 20),
        ("coding_score", "Coding Skills", 10, 100),
        ("communication_score", "Communication", 10, 100),
        ("leadership_score", "Leadership", 10, 100),
    ]

    sensitivities = []
    for feat_key, display_name, delta, cap in perturbations:
        current_val = features[feat_key]
        # Skip if already at cap
        if current_val >= cap:
            continue

        new_val = min(current_val + delta, cap)
        perturbed = copy.deepcopy(features)
        perturbed[feat_key] = new_val

        X_pert = _build_x_df(perturbed)

        new_prob = 0
        if placement_model is not None:
            new_prob = int(placement_model.predict_proba(X_pert)[0][1] * 100)

        prob_change = round(new_prob - base_prob, 1)
        sensitivities.append(
            {
                "feature": display_name,
                "current_value": current_val,
                "new_value": new_val,
                "delta_label": f"+{delta}",
                "probability_change": prob_change,
            }
        )

    # Sort by probability_change descending (highest improvement first)
    sensitivities.sort(key=lambda x: x["probability_change"], reverse=True)

    return {"base_probability": base_prob, "sensitivities": sensitivities}
