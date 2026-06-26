# -*- coding: utf-8 -*-
"""
approval_gate.py - Human in the Loop: Approval Gate

A Streamlit app that shows an email thread and an AI-generated draft reply,
then lets the user Approve, Edit, or Reject the draft before it is "sent".

Key principle: NEVER auto-send without human approval.
"""

import json
import os
from datetime import datetime, timezone

import streamlit as st

from context_builder import build_context
from draft_machine import SAMPLE_THREADS, generate_draft

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APPROVED_DRAFTS_FILE = "approved_drafts.json"
st.set_page_config(page_title="AI Email Ghostwriter - Approval Gate", layout="wide")

# ---------------------------------------------------------------------------
# Styling - dark theme
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global dark background */
    .stApp {
        background-color: #1a1a2e;
        color: #e0e0e0;
    }
    .stSidebar {
        background-color: #16213e;
    }
    /* Thread box styling */
    .thread-box {
        background-color: #0f3460;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        border-left: 4px solid #e94560;
    }
    .thread-box .sender {
        color: #e94560;
        font-weight: bold;
    }
    .thread-box .date {
        color: #8899aa;
        font-size: 0.8em;
    }
    .thread-box .body {
        color: #e0e0e0;
        margin-top: 6px;
    }
    /* Draft display box */
    .draft-box {
        background-color: #0f3460;
        border-radius: 8px;
        padding: 18px;
        border-left: 4px solid #533483;
        margin-top: 10px;
    }
    .draft-box .draft-label {
        color: #533483;
        font-weight: bold;
        margin-bottom: 8px;
    }
    /* Status indicators */
    .status-approved {
        background-color: #1b4332;
        color: #95d5b2;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        border: 1px solid #2d6a4f;
    }
    .status-rejected {
        background-color: #4a1111;
        color: #e5989b;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        border: 1px solid #9b2226;
    }
    .status-editing {
        background-color: #3e2a1a;
        color: #f4d06f;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        border: 1px solid #b8860b;
    }
    /* Metadata headers */
    .section-header {
        color: #e94560;
        font-size: 1.1em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subject-line {
        color: #e94560;
        font-size: 1.0em;
        font-weight: 600;
        margin-bottom: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Helper: load / save approved drafts
# ---------------------------------------------------------------------------
def load_approved_drafts() -> list:
    try:
        with open(APPROVED_DRAFTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_approved_draft(draft_data: dict) -> None:
    drafts = load_approved_drafts()
    drafts.append(draft_data)
    with open(APPROVED_DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2)


# ---------------------------------------------------------------------------
# Helper: get API key
# ---------------------------------------------------------------------------
def get_api_key() -> str:
    """Try st.secrets first, then os.environ, then fall back to None."""
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY", "")


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "current_draft" not in st.session_state:
    st.session_state.current_draft = ""
if "status" not in st.session_state:
    st.session_state.status = "none"  # none | approved | editing | rejected
if "selected_thread_idx" not in st.session_state:
    st.session_state.selected_thread_idx = 0
if "generation_count" not in st.session_state:
    st.session_state.generation_count = 0
if "edit_text" not in st.session_state:
    st.session_state.edit_text = ""
if "rejected_text" not in st.session_state:
    st.session_state.rejected_text = ""

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
st.title("Approval Gate - AI Email Ghostwriter")
st.markdown("**Never auto-send without human approval.**")

# ---------------------------------------------------------------------------
# API Key handling
# ---------------------------------------------------------------------------
api_key = get_api_key()
if not api_key:
    st.warning("GROQ_API_KEY not found. Enter it below or set it in st.secrets / environment.")
    api_key = st.text_input("GROQ API Key", type="password", key="api_key_input")
    if not api_key:
        st.stop()

# ---------------------------------------------------------------------------
# Sidebar - Thread Selection
# ---------------------------------------------------------------------------
st.sidebar.header("Email Thread Selection")

thread_options = [f"{t['subject']} ({len(t['messages'])} msgs)" for t in SAMPLE_THREADS]
selected_label = st.sidebar.selectbox(
    "Choose a thread",
    thread_options,
    index=st.session_state.selected_thread_idx,
    key="sidebar_thread_select",
)
selected_idx = thread_options.index(selected_label)
st.session_state.selected_thread_idx = selected_idx

st.sidebar.markdown("---")
st.sidebar.markdown("**Or paste custom JSON:**")
custom_json = st.sidebar.text_area(
    "Custom thread JSON",
    height=180,
    placeholder='{"subject": "...", "messages": [...]}',
)

col1, col2 = st.sidebar.columns([1, 1])
generate_clicked = col1.button("Generate Draft", type="primary")
col2.button("Regenerate", on_click=lambda: setattr(st.session_state, "generation_count", 0))

# ---------------------------------------------------------------------------
# Resolve the thread to use
# ---------------------------------------------------------------------------
if custom_json.strip():
    try:
        active_thread = json.loads(custom_json.strip())
        if "subject" not in active_thread or "messages" not in active_thread:
            st.sidebar.error("Custom JSON must contain 'subject' and 'messages' keys.")
            active_thread = SAMPLE_THREADS[selected_idx]
    except json.JSONDecodeError:
        st.sidebar.error("Invalid JSON. Falling back to selected thread.")
        active_thread = SAMPLE_THREADS[selected_idx]
else:
    active_thread = SAMPLE_THREADS[selected_idx]

# ---------------------------------------------------------------------------
# Layout - two columns
# ---------------------------------------------------------------------------
left_col, right_col = st.columns([1, 1])

# ====== LEFT COLUMN: THREAD HISTORY ======
with left_col:
    st.markdown('<div class="section-header">Email Thread</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="subject-line">{active_thread["subject"]}</div>',
        unsafe_allow_html=True,
    )

    for msg in active_thread["messages"]:
        st.markdown(
            f"""
            <div class="thread-box">
                <div class="sender">{msg["sender"]}</div>
                <div class="date">{msg["date"]}</div>
                <div class="body">{msg["body"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ====== RIGHT COLUMN: DRAFT & ACTIONS ======
with right_col:
    st.markdown('<div class="section-header">Draft Reply</div>', unsafe_allow_html=True)

    # -- Generate Draft --
    if generate_clicked:
        with st.spinner("Generating draft with Groq AI ..."):
            context = build_context(active_thread)
            draft = generate_draft(context, api_key)
        st.session_state.current_draft = draft
        st.session_state.status = "none"
        st.session_state.generation_count += 1
        st.session_state.edit_text = ""
        st.session_state.rejected_text = ""
        st.rerun()

    # -- Show draft (if one exists) --
    if st.session_state.current_draft:
        st.markdown(
            f"""
            <div class="draft-box">
                <div class="draft-label">AI-Generated Draft (generation #{st.session_state.generation_count})</div>
                <div>{st.session_state.current_draft}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ------------------------------------------------------------------
        # Status display
        # ------------------------------------------------------------------
        status = st.session_state.status
        if status == "approved":
            st.markdown(
                '<div class="status-approved">Approved - ready to send</div>',
                unsafe_allow_html=True,
            )
            st.success("Draft has been approved and saved.")
        elif status == "rejected":
            st.markdown(
                '<div class="status-rejected">Rejected - draft discarded</div>',
                unsafe_allow_html=True,
            )
            st.error("This draft has been rejected. Regenerate or select a different thread.")
        elif status == "editing":
            st.markdown(
                '<div class="status-editing">Editing mode</div>',
                unsafe_allow_html=True,
            )

        # ------------------------------------------------------------------
        # Action buttons (only show when not already approved)
        # ------------------------------------------------------------------
        if status != "approved":
            # Always show the three action buttons when not editing
            if status != "editing":
                action_cols = st.columns([1, 1, 1])
                with action_cols[0]:
                    if st.button("Approve", key="approve_btn", type="primary"):
                        # Save approved draft
                        approved = {
                            "thread": active_thread,
                            "draft": st.session_state.current_draft,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        save_approved_draft(approved)
                        st.session_state.status = "approved"
                        st.session_state.edit_text = ""
                        st.rerun()
                with action_cols[1]:
                    if st.button("Edit", key="edit_btn"):
                        st.session_state.status = "editing"
                        st.session_state.edit_text = st.session_state.current_draft
                        st.rerun()
                with action_cols[2]:
                    if st.button("Reject", key="reject_btn"):
                        st.session_state.status = "rejected"
                        st.session_state.rejected_text = st.session_state.current_draft
                        st.rerun()

            # ------------------------------------------------------------------
            # EDITING MODE: show text area + approve button
            # ------------------------------------------------------------------
            if status == "editing":
                edited_text = st.text_area(
                    "Edit the draft:",
                    value=st.session_state.edit_text,
                    height=200,
                    key="edit_text_area",
                )
                st.session_state.edit_text = edited_text

                col_save, col_cancel = st.columns([1, 1])
                with col_save:
                    if st.button("Approve Edited Version", type="primary", key="approve_edit_btn"):
                        st.session_state.current_draft = edited_text
                        approved = {
                            "thread": active_thread,
                            "draft": edited_text,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        save_approved_draft(approved)
                        st.session_state.status = "approved"
                        st.session_state.edit_text = ""
                        st.rerun()
                with col_cancel:
                    if st.button("Cancel Edit", key="cancel_edit_btn"):
                        st.session_state.status = "none"
                        st.session_state.edit_text = ""
                        st.rerun()

    else:
        st.info("Select a thread from the sidebar and click **Generate Draft**.")

# ---------------------------------------------------------------------------
# Footer: Summary
# ---------------------------------------------------------------------------
st.markdown("---")
approved_count = len(load_approved_drafts())
st.markdown(f"**Approved drafts saved:** `{approved_count}` in `{APPROVED_DRAFTS_FILE}`")
st.caption("The approval gate pattern keeps a human in the loop for every AI-generated action.")