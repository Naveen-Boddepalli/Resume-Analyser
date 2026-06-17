import os
import uuid
import json
import joblib
import pandas as pd
from typing import Optional
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

from parser import parse_resume
from feature_mapper import estimate_coding_score, estimate_communication_score, estimate_leadership_score
from explainer import get_shap_values
from llm import generate_recommendations
from config import SUPABASE_URL, SUPABASE_KEY

app = FastAPI(title="AI Placement Readiness Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load Models
models_dir = os.path.join(os.path.dirname(__file__), '../models')
try:
    placement_model = joblib.load(os.path.join(models_dir, 'placement_model.pkl'))
    salary_low_model = joblib.load(os.path.join(models_dir, 'salary_low_model.pkl'))
    salary_high_model = joblib.load(os.path.join(models_dir, 'salary_high_model.pkl'))
except Exception as e:
    print("Warning: Could not load models", e)
    placement_model, salary_low_model, salary_high_model = None, None, None

def update_job_status(job_id: str, status: str, result: Optional[dict] = None):
    try:
        data = {"status": status}
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
            return {"status": job["status"], "result": job.get("result")}
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
        X_df = pd.DataFrame([{
            "cgpa": features["cgpa"],
            "internships_count": features["internships_count"],
            "projects_count": features["projects_count"],
            "coding_skill_score": features["coding_score"],
            "communication_skill_score": features["communication_score"],
            "leadership_score": features["leadership_score"],
            "college_tier": features["college_tier"],
            "branch": features["branch"]
        }])

        prob = 0
        salary_low = 0
        salary_high = 0

        if placement_model is not None:
            # get placement probability (class 1)
            prob = int(placement_model.predict_proba(X_df)[0][1] * 100)
            salary_low = round(salary_low_model.predict(X_df)[0], 1)
            salary_high = round(salary_high_model.predict(X_df)[0], 1)

        features['placement_probability'] = prob
        features['salary_low'] = salary_low
        features['salary_high'] = salary_high
        
        # 3. Explain (SHAP equivalent)
        shap_results = get_shap_values(placement_model, X_df)
        
        # 4. LLM Recommendations
        recommendations_str = generate_recommendations(features, shap_results)
        try:
            recommendations = json.loads(recommendations_str).get("recommendations", [])
        except:
            recommendations = []

        final_result = {
            "features": features,
            "analysis": shap_results,
            "recommendations": recommendations
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
async def upload_resume(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    
    file_path = f"temp_{job_id}_{file.filename}"
    storage_path = f"{job_id}/{file.filename}"
    
    content = await file.read()
    
    # 1. Save locally for parser
    with open(file_path, "wb") as buffer:
        buffer.write(content)
        
    # 2. Upload to Supabase Storage
    try:
        supabase.storage.from_("resumes").upload(storage_path, content, file_options={"content-type": file.content_type})
    except Exception as e:
        print(f"Failed to upload to Supabase storage: {e}")
        
    # 3. Create job in Supabase database
    try:
        supabase.table("jobs").insert({"id": job_id, "status": "pending", "result": None}).execute()
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to insert job into DB: {str(e)}")
    
    background_tasks.add_task(process_resume, job_id, file_path, storage_path)
    
    return {"job_id": job_id, "status": "pending"}

@app.get("/result/{job_id}")
async def get_result(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/report/{job_id}")
async def get_report(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        return {"status": job["status"], "message": "Report not ready yet"}
    
    res = job["result"]
    return {
        "readiness_summary": "Good" if res["features"].get("coding_score", 0) > 60 else "Needs Improvement",
        "details": res
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
async def demo_endpoint(request: DemoRequest):
    features = request.model_dump()
    
    if features.get('coding_score') is None:
        features['coding_score'] = estimate_coding_score(features)
    if features.get('communication_score') is None:
        features['communication_score'] = estimate_communication_score(features)
    if features.get('leadership_score') is None:
        features['leadership_score'] = estimate_leadership_score(features)
    
    X_df = pd.DataFrame([{
        "cgpa": features["cgpa"],
        "internships_count": features["internships_count"],
        "projects_count": features["projects_count"],
        "coding_skill_score": features["coding_score"],
        "communication_skill_score": features["communication_score"],
        "leadership_score": features["leadership_score"],
        "college_tier": features["college_tier"],
        "branch": features["branch"]
    }])

    prob = 0
    salary_low = 0
    salary_high = 0

    if placement_model is not None:
        prob = int(placement_model.predict_proba(X_df)[0][1] * 100)
        salary_low = round(salary_low_model.predict(X_df)[0], 1)
        salary_high = round(salary_high_model.predict(X_df)[0], 1)

    features['placement_probability'] = prob
    features['salary_low'] = salary_low
    features['salary_high'] = salary_high
        
    shap_results = get_shap_values(placement_model, X_df)
    recommendations_str = generate_recommendations(features, shap_results)
    try:
        recommendations = json.loads(recommendations_str).get("recommendations", [])
    except:
        recommendations = []
        
    return {
        "features": features,
        "analysis": shap_results,
        "recommendations": recommendations
    }
