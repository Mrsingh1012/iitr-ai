from fastapi.testclient import TestClient

from job_discovery_agent.api import app
from job_discovery_agent.service import JobDiscoveryService


# ---------------------------------------------------------------------------
# Service unit tests
# ---------------------------------------------------------------------------

class TestJobDiscoveryService:
    """Unit tests for JobDiscoveryService business logic."""""

    def test_generates_application_package(self):
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

    def test_search_jobs_returns_matched_roles(self):
        service = JobDiscoveryService()

        jobs = service.search_jobs(
            profile={
                "name": "Ravi",
                "skills": ["Python", "SQL"],
                "experience_years": 2,
                "location": "Mumbai",
            },
            preferences={
                "roles": ["Backend Engineer", "Data Engineer"],
                "locations": ["Mumbai"],
            },
        )

        assert len(jobs) == 2  # one per requested role, capped at 3
        assert jobs[0]["title"] == "Backend Engineer"
        assert jobs[1]["title"] == "Data Engineer"
        assert jobs[0]["location"] == "Mumbai"

    def test_search_jobs_defaults_role_and_location_when_empty(self):
        service = JobDiscoveryService()

        # When profile has no location key and no preference, it falls back to "Remote"
        jobs = service.search_jobs(
            profile={"name": "Test", "skills": [], "experience_years": 0},
            preferences={},
        )

        assert len(jobs) == 1
        assert jobs[0]["title"] == "Software Engineer"  # default role
        assert jobs[0]["location"] == "Remote"           # default location

    def test_search_jobs_caps_at_three_results(self):
        service = JobDiscoveryService()

        jobs = service.search_jobs(
            profile={"name": "Cap", "skills": [], "experience_years": 0, "location": ""},
            preferences={"roles": ["A", "B", "C", "D", "E"]},
        )

        assert len(jobs) == 3  # capped

    def test_analyze_job_description_returns_match_score(self):
        service = JobDiscoveryService()

        result = service.analyze_job_description(
            profile={"name": "Neha", "skills": ["Python", "Docker", "Kubernetes"]},
            job_description="We need a Python developer with Docker experience.",
        )

        assert result["match_score"] >= 30
        assert "python" in result["highlights"][0].lower()
        assert "docker" in result["highlights"][1].lower()
        assert "kubernetes" not in " ".join(result["highlights"]).lower()  # not in description

    def test_analyze_job_description_no_skills_match(self):
        service = JobDiscoveryService()

        result = service.analyze_job_description(
            profile={"name": "NoMatch", "skills": ["Rust", "Go"]},
            job_description="We need a Python developer.",
        )

        assert result["match_score"] == 30  # base score only
        assert result["highlights"] == []

    def test_analyze_job_description_score_capped_at_100(self):
        service = JobDiscoveryService()

        many_skills = [f"skill_{i}" for i in range(20)]
        description = " ".join(many_skills)
        result = service.analyze_job_description(
            profile={"name": "Overflow", "skills": many_skills},
            job_description=description,
        )

        assert result["match_score"] == 100

    def test_customize_resume_uses_top_job(self):
        service = JobDiscoveryService()

        result = service.customize_resume(
            profile={"name": "Amit", "skills": ["Python", "FastAPI"]},
            matched_jobs=[
                {"title": "Python Developer", "company": "X", "location": "Delhi", "match_score": 90},
                {"title": "Backend Engineer", "company": "Y", "location": "Delhi", "match_score": 80},
            ],
        )

        assert result["resume"]["headline"] == "Tailored for Python Developer"
        assert "Python" in result["resume"]["summary"]
        assert "Python Developer" in result["resume"]["cover_letter"]

    def test_customize_resume_with_empty_jobs_falls_back(self):
        service = JobDiscoveryService()

        result = service.customize_resume(
            profile={"name": "Fallback", "skills": ["Java"]},
            matched_jobs=[],
        )

        assert result["resume"]["headline"] == "Tailored for Software Engineer"  # fallback title
        assert "Java" in result["resume"]["summary"]

    def test_experience_years_boosts_match_score(self):
        service = JobDiscoveryService()

        jobs_low = service.search_jobs(
            profile={"name": "Junior", "skills": [], "experience_years": 0, "location": ""},
            preferences={"roles": ["Engineer"]},
        )
        jobs_high = service.search_jobs(
            profile={"name": "Senior", "skills": [], "experience_years": 5, "location": ""},
            preferences={"roles": ["Engineer"]},
        )

        assert jobs_high[0]["match_score"] > jobs_low[0]["match_score"]

    def test_skill_bonus_for_python_fastapi_sql(self):
        service = JobDiscoveryService()

        jobs_with_skills = service.search_jobs(
            profile={"name": "Skilled", "skills": ["Python", "FastAPI", "SQL"], "experience_years": 0, "location": ""},
            preferences={"roles": ["Engineer"]},
        )
        jobs_without = service.search_jobs(
            profile={"name": "Plain", "skills": ["Java"], "experience_years": 0, "location": ""},
            preferences={"roles": ["Engineer"]},
        )

        assert jobs_with_skills[0]["match_score"] > jobs_without[0]["match_score"]

    def test_python_role_prefix_bonus(self):
        service = JobDiscoveryService()

        jobs = service.search_jobs(
            profile={"name": "PyDev", "skills": [], "experience_years": 0, "location": ""},
            preferences={"roles": ["Python Developer"]},
        )

        # Python role prefix adds +10
        assert jobs[0]["match_score"] >= 80  # 70 base + 10 prefix


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestJobDiscoveryAPI:
    """Integration tests for FastAPI endpoints."""""

    client = TestClient(app)

    def test_profile_endpoint_accepts_payload(self):
        response = self.client.post(
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

    def test_profile_endpoint_missing_profile_returns_400(self):
        response = self.client.post("/api/profile", json={"preferences": {}})
        assert response.status_code == 400
        assert "Missing profile" in response.json()["detail"]

    def test_search_endpoint_returns_jobs(self):
        response = self.client.post(
            "/api/search",
            json={
                "profile": {"name": "Sneha", "skills": ["Python"], "experience_years": 1, "location": "Pune"},
                "preferences": {"roles": ["Data Scientist"]},
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert "matched_jobs" in body
        assert len(body["matched_jobs"]) >= 1
        assert body["matched_jobs"][0]["title"] == "Data Scientist"

    def test_search_endpoint_missing_profile_returns_400(self):
        response = self.client.post("/api/search", json={"preferences": {}})
        assert response.status_code == 400
        assert "Missing profile" in response.json()["detail"]

    def test_analyze_endpoint_returns_analysis(self):
        response = self.client.post(
            "/api/analyze",
            json={
                "profile": {"name": "Kiran", "skills": ["Python", "ML"]},
                "job_description": "Looking for a Python ML engineer.",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert "match_score" in body
        assert "highlights" in body
        assert body["match_score"] >= 30

    def test_analyze_endpoint_missing_fields_returns_400(self):
        response = self.client.post("/api/analyze", json={"profile": {}})
        assert response.status_code == 400
        assert "Missing" in response.json()["detail"]

    def test_customize_endpoint_returns_customization(self):
        response = self.client.post(
            "/api/customize",
            json={
                "profile": {"name": "Arun", "skills": ["Java", "Spring"]},
                "matched_jobs": [
                    {"title": "Java Developer", "company": "X", "location": "Noida", "match_score": 85}
                ],
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert "resume" in body
        assert body["resume"]["headline"] == "Tailored for Java Developer"

    def test_customize_endpoint_missing_fields_returns_400(self):
        response = self.client.post("/api/customize", json={"profile": {}})
        assert response.status_code == 400
        assert "Missing" in response.json()["detail"]