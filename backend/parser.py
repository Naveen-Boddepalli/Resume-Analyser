import fitz  # PyMuPDF
from docx import Document
import re

def parse_pdf(file_path: str) -> dict:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
         blocks = page.get_text("blocks")
         for block in blocks:
             text += block[4] + "\n"
    return extract_features(text)

def parse_docx(file_path: str) -> dict:
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return extract_features(text)

def extract_features(text: str) -> dict:
    text_lower = text.lower()
    
    # Very basic dummy extraction logic
    cgpa = 0.0
    cgpa_match = re.search(r'cgpa[:\s]*([0-9]+\.[0-9]+)', text_lower)
    if cgpa_match:
        try:
            cgpa = float(cgpa_match.group(1))
        except:
            pass
            
    projects_count = text_lower.count('project') // 2  # arbitrary logic for demo
    internships_count = text_lower.count('internship') // 2
    certifications_count = text_lower.count('certification') // 2
    
    skills = ["python", "java", "c++", "machine learning", "react", "sql", "aws", "docker"]
    skills_list = [skill for skill in skills if skill in text_lower]

    return {
        "cgpa": cgpa,
        "projects_count": projects_count,
        "internships_count": internships_count,
        "certifications_count": certifications_count,
        "skills_list": skills_list,
        "raw_text": text
    }

def parse_resume(file_path: str) -> dict:
    if file_path.lower().endswith('.pdf'):
        return parse_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return parse_docx(file_path)
    else:
        # Fallback text parsing if needed
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return extract_features(text)
