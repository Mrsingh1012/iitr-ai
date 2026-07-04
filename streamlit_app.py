import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000/api"

st.title("AI Job Discovery Agent")
st.write("Enter your profile and job preferences to discover relevant job opportunities.")

with st.form("profile_form"):
    name = st.text_input("Name")
    location = st.text_input("Location", "Remote")
    experience_years = st.number_input("Experience (years)", min_value=0, max_value=30, value=1)
    skills = st.text_area("Skills (comma separated)", "Python, FastAPI, SQL")
    roles = st.text_area("Target roles (comma separated)", "Python Developer")
    salary_min = st.number_input("Minimum salary", min_value=0, value=1000000)
    submitted = st.form_submit_button("Generate Application Package")

if submitted:
    profile = {
        "name": name,
        "location": location,
        "experience_years": experience_years,
        "skills": [skill.strip() for skill in skills.split(",") if skill.strip()],
    }
    preferences = {
        "roles": [role.strip() for role in roles.split(",") if role.strip()],
        "locations": [location],
        "salary_min": salary_min,
    }

    response = requests.post(
        f"{API_BASE}/profile",
        json={"profile": profile, "preferences": preferences},
        timeout=15,
    )

    if response.ok:
        data = response.json()
        st.subheader("Matched Jobs")
        for job in data["matched_jobs"]:
            st.markdown(f"**{job['title']}** at {job['company']} — {job['location']}")
            st.write(f"Match score: {job['match_score']}\n{job['summary']}")

        st.subheader("Customized Resume")
        st.write(data["customization"]["resume"]["headline"])
        st.write(data["customization"]["resume"]["summary"])
        st.write(data["customization"]["resume"]["cover_letter"])
    else:
        st.error(f"API error: {response.status_code} - {response.text}")
