from fastapi.testclient import TestClient

from job_discovery_agent.api import app
from job_discovery_agent.service import JobDiscoveryService


def test_job_discovery_service_generates_application_package():
    service = JobDiscoveryService()

    result = service.generate_application_package(
        profile={
            "name": "Asha",
            "skills": ["Python", "FastAPI", "SQL"],
            "experience_years": 3,
            "location": "Bengaluru",
        },
        preferences={
            "roles": ["Python Developer"],
            "locations": ["Bengaluru"],
            "salary_min": 1200000,
        },
    )

    assert result["profile"]["name"] == "Asha"
    assert len(result["matched_jobs"]) >= 1
    assert result["matched_jobs"][0]["title"] == "Python Developer"
    assert "cover_letter" in result["customization"]["resume"]


def test_profile_endpoint_accepts_payload():
    client = TestClient(app)
    response = client.post(
        "/api/profile",
        json={
            "profile": {
                "name": "Riya",
                "skills": ["Python", "React"],
                "experience_years": 2,
                "location": "Hyderabad",
            },
            "preferences": {
                "roles": ["Frontend Engineer"],
                "locations": ["Hyderabad"],
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["profile"]["name"] == "Riya"
