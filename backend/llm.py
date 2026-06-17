import json
import requests
import time

from config import MISTRAL_API_KEY, MISTRAL_API_URL

def generate_recommendations(features: dict, shap_results: dict) -> dict:
    prompt = f"""
    Based on the following resume features and analysis, provide 4 actionable recommendations to improve placement readiness.
    Return ONLY a JSON object with a 'recommendations' list containing exactly 4 strings.
    
    Features: {json.dumps(features)}
    Analysis: {json.dumps(shap_results)}
    """
    
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": "You are an expert career advisor and technical recruiter. Output only a valid JSON object."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        # Add retry logic for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.post(MISTRAL_API_URL, json=payload, headers=headers)
            if response.status_code == 429 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s...
                continue
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"LLM Recommendation failed: {e}")
        return '{"recommendations": ["Improve coding skills by practicing on LeetCode", "Build more full-stack projects", "Apply for internships to gain industry experience", "Practice mock interviews to improve communication"]}'
