#!/usr/bin/env python3
"""
hello_jobs.py - Saves a list of 5 fake job titles and companies to a CSV file.
"""

import csv

# Fake job listings data
jobs = [
    ("Senior Software Engineer", "TechNova Solutions"),
    ("Data Scientist", "DataMinds Analytics"),
    ("UX/UI Designer", "Creative Pulse Studio"),
    ("DevOps Engineer", "CloudFirst Infrastructure"),
    ("Product Manager", "InnovateTech Labs"),
]

# Write to CSV file
with open("jobs.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Job Title", "Company"])
    writer.writerows(jobs)

print("Jobs saved to jobs.csv")