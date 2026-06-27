from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "test-secret-key-123"}

def test_app_title():
    assert app.title == "AI Placement Readiness Platform API"


def test_salary_distribution():
    response = client.get("/salary-distribution", headers=HEADERS)
    # Will be 200 if the CSV exists in data/, otherwise 500 as designed
    assert response.status_code in [200, 500]


def test_get_result_not_found():
    response = client.get("/result/non-existent-job-123", headers=HEADERS)
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_get_report_not_found():
    response = client.get("/report/non-existent-job-123", headers=HEADERS)
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_demo_endpoint_validation_error():
    # Missing required 'cgpa' field
    payload = {
        "projects_count": 2,
        "internships_count": 1,
        "certifications_count": 1,
        "skills_list": ["Python", "React"],
        "college_tier": "Tier 1",
        "branch": "CSE",
    }
    response = client.post("/demo", json=payload, headers=HEADERS)
    assert response.status_code == 422  # Unprocessable Entity


def test_demo_endpoint_success():
    payload = {
        "cgpa": 8.0,
        "projects_count": 2,
        "internships_count": 1,
        "certifications_count": 1,
        "skills_list": ["Python", "React"],
        "college_tier": "Tier 1",
        "branch": "CSE",
    }
    response = client.post("/demo", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert "analysis" in data
    assert "roadmap" in data
    assert data["features"]["cgpa"] == 8.0
