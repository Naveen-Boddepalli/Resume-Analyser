import fitz  # PyMuPDF
from docx import Document
import re
import json
import requests
import time
from config import MISTRAL_API_KEY, MISTRAL_API_URL


def parse_pdf(file_path: str) -> dict:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        blocks = page.get_text("blocks")
        for block in blocks:
            text += block[4] + "\n"
    return llm_extract_features(text)


def parse_docx(file_path: str) -> dict:
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return llm_extract_features(text)


def llm_extract_features(text: str) -> dict:
    text_lower = text.lower()

    # Resume Validation Check
    resume_keywords = [
        "education",
        "experience",
        "skills",
        "project",
        "internship",
        "resume",
        "profile",
        "cgpa",
        "university",
        "college",
        "degree",
    ]
    keyword_matches = sum(1 for kw in resume_keywords if kw in text_lower)

    if keyword_matches < 2:
        raise ValueError(
            "Invalid resume format: The uploaded document does not appear to be a valid resume."
        )

    prompt = f"""
    You are an expert resume parser. Extract the following information from the resume text below and return it strictly as a valid JSON object.
    
    Required JSON structure:
    {{
      "cgpa": <float, out of 10.0, default 0.0 if not found>,
      "projects_count": <int, total number of distinct projects, default 0>,
      "internships_count": <int, total number of distinct internships/work experiences, default 0>,
      "certifications_count": <int, total number of distinct certifications, default 0>,
      "skills_list": [<list of strings, exact technical skills found (e.g. "python", "react", "aws")>],
      "college_tier": <string, one of: "Tier 1", "Tier 2", "Tier 3" based on the university prestige. Default "Tier 2">,
      "branch": <string, degree major abbreviation e.g., "CSE", "IT", "ECE", "EEE", "Mechanical". Default "CSE">
    }}
    
    Resume Text:
    {text[:4000]}
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
                "content": "You are a robust JSON extraction API. You must return ONLY raw JSON matching the requested structure. No markdown, no explanations.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.post(MISTRAL_API_URL, json=payload, headers=headers)  # type: ignore
            if response.status_code == 429 and attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            data = json.loads(response.json()["choices"][0]["message"]["content"])

            return {
                "cgpa": float(data.get("cgpa", 0.0)),
                "projects_count": int(data.get("projects_count", 0)),
                "internships_count": int(data.get("internships_count", 0)),
                "certifications_count": int(data.get("certifications_count", 0)),
                "skills_list": [str(s).lower() for s in data.get("skills_list", [])],
                "college_tier": str(data.get("college_tier", "Tier 2")),
                "branch": str(data.get("branch", "CSE")).upper(),
                "raw_text": text,
            }
        raise Exception("Max retries exceeded for LLM parsing")
    except Exception as e:
        print(f"LLM Parsing failed, falling back to regex: {e}")
        return extract_features_fallback(text)


def extract_features_fallback(text: str) -> dict:
    text_lower = text.lower()

    # Very basic dummy extraction logic
    cgpa = 0.0
    cgpa_match = re.search(r"cgpa[:\s]*([0-9]+\.[0-9]+)", text_lower)
    if cgpa_match:
        try:
            cgpa = float(cgpa_match.group(1))
        except Exception:
            pass

    projects_count = text_lower.count("project") // 2
    internships_count = text_lower.count("internship") // 2
    certifications_count = text_lower.count("certification") // 2

    skills = [
        "python",
        "java",
        "c++",
        "machine learning",
        "react",
        "sql",
        "aws",
        "docker",
    ]
    skills_list = [skill for skill in skills if skill in text_lower]

    return {
        "cgpa": cgpa,
        "projects_count": projects_count,
        "internships_count": internships_count,
        "certifications_count": certifications_count,
        "skills_list": skills_list,
        "college_tier": "Tier 2",
        "branch": "CSE",
        "raw_text": text,
    }


def parse_resume(file_path: str) -> dict:
    if file_path.lower().endswith(".pdf"):
        return parse_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        return parse_docx(file_path)
    else:
        # Fallback text parsing if needed
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return llm_extract_features(text)
