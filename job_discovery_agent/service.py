from __future__ import annotations

from typing import Any, Dict, List


class JobDiscoveryService:
    """A lightweight service that mimics the autonomous job discovery workflow."""

    def generate_application_package(self, profile: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        matched_jobs = self._discover_jobs(profile, preferences)
        customization = self._customize_resume(profile, matched_jobs)
        return {
            "profile": profile,
            "preferences": preferences,
            "matched_jobs": matched_jobs,
            "customization": customization,
        }

    def search_jobs(self, profile: Dict[str, Any], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self._discover_jobs(profile, preferences)

    def customize_resume(self, profile: Dict[str, Any], matched_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._customize_resume(profile, matched_jobs)

    def analyze_job_description(self, profile: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        skills = [skill.lower() for skill in profile.get("skills", [])]
        score = 0
        for skill in skills:
            if skill in job_description.lower():
                score += 10
        score = min(100, 30 + score)
        return {
            "job_description": job_description,
            "match_score": score,
            "highlights": [f"Matches skill: {skill}" for skill in skills if skill in job_description.lower()],
        }

    def _discover_jobs(self, profile: Dict[str, Any], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        role_preferences = preferences.get("roles", []) or ["Software Engineer"]
        location_preferences = preferences.get("locations", []) or [profile.get("location", "Remote")]
        skills = profile.get("skills", [])
        experience_years = profile.get("experience_years", 0)

        matched_roles = []
        for role in role_preferences:
            score = 70 + min(experience_years, 5) * 4
            if any(skill.lower() in {"python", "fastapi", "sql"} for skill in skills):
                score += 8
            if role.lower().startswith("python"):
                score += 10
            matched_roles.append(
                {
                    "title": role,
                    "company": "Example Labs",
                    "location": location_preferences[0] if location_preferences else "Remote",
                    "match_score": min(score, 99),
                    "salary_min": preferences.get("salary_min", 1000000),
                    "summary": f"Good fit for {profile.get('name', 'the candidate')} based on their skills and experience.",
                }
            )

        return matched_roles[:3]

    def _customize_resume(self, profile: Dict[str, Any], matched_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        top_job = matched_jobs[0] if matched_jobs else {"title": "Software Engineer"}
        skills = ", ".join(profile.get("skills", []))
        return {
            "resume": {
                "headline": f"Tailored for {top_job['title']}",
                "summary": f"Experienced professional with expertise in {skills}.",
                "cover_letter": f"Dear Hiring Team, I am excited to apply for the {top_job['title']} role. My background in {skills} aligns well with your team.",
            },
            "notes": [f"Prioritize {top_job['title']} opportunities."],
        }
