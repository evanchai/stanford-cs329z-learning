"""Problem 1 (priority), v1 — Ning's plan.

Prompt = the rubric from data/priority_rubric.md; the model must reply with
JSON {"category": ..., "reason": ...}; the code parses that JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

RUBRIC = (Path(__file__).resolve().parents[2] / "data" / "priority_rubric.md").read_text(encoding="utf-8")

SYSTEM = (
    "Classify the priority of an email using this rubric.\n\n"
    f"{RUBRIC}\n\n"
    "## How to read deadlines\n\n"
    "- A deadline can be implied, not only stated. \"Please have the numbers to me before you leave tonight\" "
    "or \"make sure this gets done today\" sets a same-day deadline.\n"
    "- Only the time by which THIS recipient must act counts. A date in the email that belongs to "
    "something else (\"the conference is on Friday\", \"the report ships Thursday\") is not the recipient's deadline.\n"
    "- When the email gives no deadline and implies none, it is not urgent, however important the "
    "work sounds or however eager the requester is. A sentence like \"the client called this morning "
    "asking about it\" says when the request arrived, not when it is due.\n\n"
    "Reply with JSON only, in exactly this format:\n"
    '{"category": "urgent" | "normal" | "ignore" | "unknown", "reason": "one-sentence reason"}'
)

CATEGORIES = ("urgent", "normal", "ignore", "unknown")


def run_priority(email: dict, lm) -> dict:
    user = (
        f"From: {email.get('from')}\n"
        f"To: {', '.join(email.get('to') or [])}\n"
        f"Date: {email.get('date')}\n"
        f"Subject: {email.get('subject')}\n\n"
        f"{email.get('body')}"
    )
    reply = lm([{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
    try:
        data = json.loads(reply)
        category = str(data.get("category", "")).lower()
        reason = str(data.get("reason", "")).strip()
    except Exception:
        return {"category": "unknown", "reason": "The reply was not valid JSON."}
    if category not in CATEGORIES:
        category = "unknown"
    return {"category": category, "reason": reason or "No reason given."}
