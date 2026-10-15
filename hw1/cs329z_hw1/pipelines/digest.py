"""Problem 2 (daily_digest), v1 — Ning's plan.

1. classify every email of the day with Problem 1 (concurrently)
2. drop ignore (unknown counts as normal)
3. send the urgent emails to the model, which writes the summary:
   at most 300 words, naming the company, project or site of each item
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from cs329z_hw1.pipelines.priority import run_priority

SYSTEM = (
    "Write a morning digest of today's urgent emails for a busy employee. "
    "The digest must be at most 300 words. "
    "For every email, name the company, project or site it is about."
)


def run_daily_digest(emails: list[dict], lm) -> str:
    if not emails:
        return "No emails today."
    with ThreadPoolExecutor(max_workers=8) as pool:
        labels = list(pool.map(lambda e: run_priority(e, lm)["category"], emails))
    kept = [(e, "normal" if c == "unknown" else c) for e, c in zip(emails, labels) if c != "ignore"]
    urgent = [e for e, c in kept if c == "urgent"]
    if not urgent:
        return "No urgent emails today."
    text = "\n\n---\n\n".join(
        f"From: {e.get('from')}\nSubject: {e.get('subject')}\n\n{e.get('body')}" for e in urgent
    )
    reply = lm([{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}])
    return reply if isinstance(reply, str) else str(reply)
