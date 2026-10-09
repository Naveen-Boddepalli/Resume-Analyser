import os
import uuid
import json
from typing import Optional, Any
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Form,
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
from llm import evaluate_job_match
from config import SUPABASE_URL, SUPABASE_KEY

app = FastAPI(title="AI Resume Screening & Job-Matching API")

API_KEY = os.getenv("API_KEY", "test-secret-key-123")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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


def process_resume(job_id: str, file_path: str, storage_path: str, job_description: str):
    try:
        update_job_status(job_id, "processing")

        # 1. Parse resume
        parsed_data = parse_resume(file_path)

        # 2. Extract features
        features = {
            "cgpa": parsed_data.get("cgpa", 0.0),
            "projects_count": parsed_data.get("projects_count", 0),
            "internships_count": parsed_data.get("internships_count", 0),
            "certifications_count": parsed_data.get("certifications_count", 0),
            "skills": parsed_data.get("skills_list", []),
            "college_tier": parsed_data.get("college_tier", "Tier 2"),
            "branch": parsed_data.get("branch", "CSE"),
        }

        # 3. LLM Matching
        llm_response_str = evaluate_job_match(features, job_description)
        try:
            llm_result = json.loads(llm_response_str)
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            llm_result = {
                "match_score": 0,
                "decision": "Review",
                "matching_skills": [],
                "missing_skills": [],
                "summary": "Failed to parse analysis."
            }

        # Assemble response
        final_result = {
            "features": features,
            "match_score": llm_result.get("match_score", 0),
            "decision": llm_result.get("decision", "Review"),
            "matching_skills": llm_result.get("matching_skills", []),
            "missing_skills": llm_result.get("missing_skills", []),
            "summary": llm_result.get("summary", "")
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
            print(f"Failed removing {storage_path} from Supabase: {e}")


@app.post("/upload")
@limiter.limit("50/day")
async def upload_resume(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_description: str = Form(...),
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

    background_tasks.add_task(process_resume, job_id, file_path, storage_path, job_description)

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


class DemoRequest(BaseModel):
    job_description: str
    cgpa: float
    projects_count: int
    internships_count: int
    certifications_count: int
    skills_list: list[str]
    college_tier: str
    branch: str


@app.post("/demo")
@limiter.limit("20/day")
async def demo_endpoint(
    request: Request, demo_req: DemoRequest, api_key: str = Depends(get_api_key)
):
    features = demo_req.model_dump()
    job_desc = features.pop("job_description")

    llm_response_str = evaluate_job_match(features, job_desc)
    try:
        llm_result = json.loads(llm_response_str)
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        llm_result = {
            "match_score": 50,
            "decision": "Review",
            "matching_skills": [],
            "missing_skills": [],
            "summary": "Failed to analyze resume via LLM."
        }

    return {
        "features": features,
        "match_score": llm_result.get("match_score", 0),
        "decision": llm_result.get("decision", "Review"),
        "matching_skills": llm_result.get("matching_skills", []),
        "missing_skills": llm_result.get("missing_skills", []),
        "summary": llm_result.get("summary", "")
    }
