import json
import requests
import time

from config import MISTRAL_API_KEY, MISTRAL_API_URL


def generate_recommendations(features: dict, shap_results: dict) -> str:
    prompt = f"""
    Based on the following resume features and analysis, provide a 4-step week-by-week action plan to improve placement readiness.
    Return ONLY a JSON object with a 'roadmap' list containing exactly 4 objects.
    Each object must have:
    - 'timeframe': A string like "Week 1-2"
    - 'action': A detailed string describing the action to take.
    
    Features: {json.dumps(features)}
    Analysis: {json.dumps(shap_results)}
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
                "content": "You are an expert career advisor and technical recruiter. Output only a valid JSON object.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }

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
        return '{"roadmap": [{"timeframe": "Week 1-2", "action": "Complete Python DSA course"}, {"timeframe": "Week 3-4", "action": "Build a full-stack project"}, {"timeframe": "Week 5-6", "action": "Apply for internships"}, {"timeframe": "Week 7-8", "action": "Practice mock interviews"}]}'
    except Exception as e:
        print(f"LLM Recommendation failed: {e}")
        return '{"roadmap": [{"timeframe": "Week 1-2", "action": "Complete Python DSA course"}, {"timeframe": "Week 3-4", "action": "Build a full-stack project"}, {"timeframe": "Week 5-6", "action": "Apply for internships"}, {"timeframe": "Week 7-8", "action": "Practice mock interviews"}]}'
