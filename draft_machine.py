"""
Draft Machine

Generates email draft replies using the Groq API (Llama 3 70B).
Imports context from context_builder.py.

Exports:
- SAMPLE_THREADS: List of three sample email threads
- generate_draft(context, api_key): Calls Groq and returns the draft reply text
"""

import requests
from typing import Optional

# ---------------------------------------------------------------------------
# Sample threads for testing / demo
# ---------------------------------------------------------------------------
SAMPLE_THREADS = [
    {
        "subject": "Q4 Project Kickoff - Action Items",
        "messages": [
            {
                "sender": "Alice Chen",
                "date": "2026-06-20 09:15",
                "body": "Hi team, let's kick off Q4 planning. I need everyone to submit their top 3 priorities by Friday."
            },
            {
                "sender": "Bob Martinez",
                "date": "2026-06-20 10:30",
                "body": "Thanks Alice. I'll have mine ready by EOD Thursday. Quick question - are we including maintenance work in priorities or only net-new features?"
            },
            {
                "sender": "Alice Chen",
                "date": "2026-06-21 08:00",
                "body": "Great question, Bob. Let's include both but clearly label them. If you could also estimate hours per priority that would be very helpful."
            }
        ]
    },
    {
        "subject": "Client Feedback on Draft Proposal",
        "messages": [
            {
                "sender": "Sarah Kim",
                "date": "2026-06-19 14:00",
                "body": "I just got off the call with Acme Corp. They love the proposal structure but want the pricing section broken out by milestone rather than a single lump sum."
            },
            {
                "sender": "David Park",
                "date": "2026-06-19 15:45",
                "body": "That makes sense. I'll rework the pricing table this evening. Do they want hourly rates visible or just fixed milestone amounts?"
            },
            {
                "sender": "Sarah Kim",
                "date": "2026-06-20 09:30",
                "body": "Fixed milestone amounts only - they explicitly said no hourly breakdowns. Also, can we add a 'success criteria' column next to each milestone?"
            }
        ]
    },
    {
        "subject": "Intern Onboarding Schedule",
        "messages": [
            {
                "sender": "Priya Singh",
                "date": "2026-06-18 11:00",
                "body": "Our summer interns start Monday! I need a schedule for their first week - orientation, tool setup, intro meetings."
            },
            {
                "sender": "James Wilson",
                "date": "2026-06-18 13:20",
                "body": "I can handle the tool setup session (Git, IDE, internal tools) - Tuesday 10-12 works for me. How many interns are we expecting?"
            },
            {
                "sender": "Priya Singh",
                "date": "2026-06-19 07:45",
                "body": "Five interns total. James - Tuesday 10-12 sounds great. I'll put together the full schedule and share it later today. Do we need a welcome lunch?"
            }
        ]
    }
]

# ---------------------------------------------------------------------------
# Groq API helper
# ---------------------------------------------------------------------------
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def generate_draft(context: str, api_key: str, model: str = "llama3-70b-8192") -> Optional[str]:
    """
    Send the built context to Groq's Llama 3 70B and return the generated draft reply.

    Args:
        context: The formatted prompt context from context_builder.build_context()
        api_key: Groq API key
        model: Model identifier (default: llama3-70b-8192)

    Returns:
        The generated reply text, or None on failure.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional email assistant. Generate ONLY the draft reply text - no preamble, no meta-commentary."},
            {"role": "user", "content": context}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Error generating draft: {e}]"