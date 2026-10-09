import json
import requests
import time

from config import MISTRAL_API_KEY, MISTRAL_API_URL


def evaluate_job_match(features: dict, job_description: str) -> str:
    prompt = f"""
    You are an expert technical recruiter and AI resume screener.
    Evaluate the following candidate's resume features against the provided Job Description.
    
    Resume Features: {json.dumps(features)}
    Job Description: {job_description}
    
    Return ONLY a valid JSON object with the following structure:
    {{
        "match_score": (integer from 0 to 100 representing the fit),
        "decision": (string, one of: "Shortlist", "Review", "Reject"),
        "matching_skills": [(list of strings representing skills present in BOTH the resume and JD)],
        "missing_skills": [(list of strings representing critical skills in the JD that are MISSING from the resume)],
        "summary": (string, a 2-3 sentence recruiter-focused summary of the candidate's fit)
    }}
    """

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert technical recruiter. Output only a valid JSON object.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }

    fallback_json = '{"match_score": 50, "decision": "Review", "matching_skills": [], "missing_skills": [], "summary": "Failed to analyze resume via LLM."}'

    try:
        # Add retry logic for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.post(MISTRAL_API_URL, json=payload, headers=headers, timeout=15)  # type: ignore
            if response.status_code == 429 and attempt < max_retries - 1:
                time.sleep(2**attempt)  # Exponential backoff: 1s, 2s...
                continue
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        return fallback_json
    except Exception as e:
        print(f"LLM Recommendation failed: {e}")
        return fallback_json
