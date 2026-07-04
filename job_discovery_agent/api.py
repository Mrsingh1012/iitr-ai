from fastapi import FastAPI, HTTPException

from .service import JobDiscoveryService

app = FastAPI(title="AI Job Discovery Agent")
service = JobDiscoveryService()


@app.post("/api/profile")
def create_profile(payload: dict):
    profile = payload.get("profile", {})
    preferences = payload.get("preferences", {})
    if not profile:
        raise HTTPException(status_code=400, detail="Missing profile payload")

    return service.generate_application_package(profile, preferences)


@app.post("/api/search")
def search_jobs(payload: dict):
    profile = payload.get("profile", {})
    preferences = payload.get("preferences", {})
    if not profile:
        raise HTTPException(status_code=400, detail="Missing profile payload")

    return {"matched_jobs": service.search_jobs(profile, preferences)}


@app.post("/api/analyze")
def analyze_job_description(payload: dict):
    profile = payload.get("profile", {})
    job_description = payload.get("job_description", "")
    if not profile or not job_description:
        raise HTTPException(status_code=400, detail="Missing payload fields")

    return service.analyze_job_description(profile, job_description)


@app.post("/api/customize")
def customize_resume(payload: dict):
    profile = payload.get("profile", {})
    matched_jobs = payload.get("matched_jobs", [])
    if not profile or not matched_jobs:
        raise HTTPException(status_code=400, detail="Missing payload fields")

    return service.customize_resume(profile, matched_jobs)
