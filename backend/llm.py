import json
import requests

GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_recommendations(features: dict, shap_results: dict) -> dict:
    prompt = f"""
    Based on the following resume features and analysis, provide 4 actionable recommendations to improve placement readiness.
    Return ONLY a JSON object with a 'recommendations' list containing exactly 4 strings.
    
    Features: {json.dumps(features)}
    Analysis: {json.dumps(shap_results)}
    """
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are an expert career advisor and technical recruiter. Output only a valid JSON object."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return '{"recommendations": ["Improve coding skills by practicing on LeetCode", "Build more full-stack projects", "Apply for internships to gain industry experience", "Practice mock interviews to improve communication"]}'
