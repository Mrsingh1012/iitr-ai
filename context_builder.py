"""
Context Builder

Assembles a structured prompt context from:
- tone_profile.json (tone/style preferences)
- past_replies.json (historical reply examples)
- Thread history (the conversation so far)

This module is used by draft_machine.py and approval_gate.py.
"""

import json
import os
from typing import Any


def load_json(filepath: str) -> Any:
    """Load a JSON file from the given path, returning default structure on failure."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def build_context(thread: dict, tone_profile_path: str = "tone_profile.json",
                  past_replies_path: str = "past_replies.json") -> str:
    """
    Build a formatted prompt context string from a thread, tone profile, and past replies.

    Args:
        thread: dict with keys "subject" and "messages".
                Each message is a dict with "sender", "date", "body".
        tone_profile_path: path to tone_profile.json
        past_replies_path: path to past_replies.json

    Returns:
        A formatted string ready for inclusion in a Groq API prompt.
    """
    tone = load_json(tone_profile_path)
    past_replies = load_json(past_replies_path)

    sections = []

    # 1. Tone instructions
    sections.append("### TONE PROFILE")
    sections.append(f"Tone: {tone.get('tone', 'professional')}")
    sections.append(f"Formality: {tone.get('formality', 'moderate')}")
    sections.append(f"Desired length: {tone.get('length', 'concise')}")
    style = tone.get("style_notes", [])
    if style:
        sections.append("Style notes:")
        for note in style:
            sections.append(f"  - {note}")

    sections.append("")  # blank line

    # 2. Past replies (examples of style)
    if past_replies and isinstance(past_replies, list):
        sections.append("### PAST REPLY EXAMPLES")
        for i, example in enumerate(past_replies[:5], 1):
            sections.append(f"Example {i}:")
            sections.append(f"  Subject: {example.get('thread_subject', 'N/A')}")
            sections.append(f"  Original: {example.get('original_message', '')}")
            sections.append(f"  Reply: {example.get('reply', '')}")
        sections.append("")

    # 3. Thread history
    sections.append("### CURRENT THREAD")
    sections.append(f"Subject: {thread.get('subject', 'No subject')}")
    messages = thread.get("messages", [])
    if not messages:
        sections.append("(No messages in thread)")
    else:
        sections.append("Messages (oldest first):")
        for msg in messages:
            sender = msg.get("sender", "Unknown")
            date = msg.get("date", "")
            body = msg.get("body", "")
            sections.append(f"[{date}] {sender}: {body}")

    sections.append("")
    sections.append("### INSTRUCTION")
    sections.append(
        "Write a draft reply to the most recent message in the thread above. "
        "Follow the tone profile. Be concise and professional."
    )

    return "\n".join(sections)