"""Problem 12 (memory), v1 — Ning's design:
- the model decides when to call remember(fact);
- a new session loads the whole store into its system prompt (Claude Code / Codex style);
- a correction overwrites: aux_lm says which stored facts the new one replaces, and those go.
Store: <memory_dir>/memory.json, a list of {"fact", "saved_at"}.
"""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

_WORD = re.compile(r"[a-z0-9]+")

REPLACE_SYSTEM = (
    "You maintain a list of facts about one user. A new fact is being saved. Which of the numbered existing "
    "facts does it replace, because it is about the same thing (a correction or an update)? Reply with the "
    "numbers separated by commas, or NONE."
)


class MemoryStore:
    def __init__(self, directory, aux_lm=None) -> None:
        self.path = Path(directory) / "memory.json"
        self.aux_lm = aux_lm
        self._lock = threading.Lock()

    def facts(self) -> list[dict]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save(self, facts: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(facts, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.path)

    def _replaced(self, fact: str, facts: list[dict]) -> set[int]:
        if not facts or self.aux_lm is None:
            return set()
        listing = "\n".join(f"{i + 1}. {f['fact']}" for i, f in enumerate(facts))
        try:
            reply = str(self.aux_lm([{"role": "system", "content": REPLACE_SYSTEM},
                                     {"role": "user", "content": f"Existing facts:\n{listing}\n\nNew fact: {fact}"}]))
        except Exception:
            return set()
        if "none" in reply.lower():
            return set()
        return {int(n) - 1 for n in re.findall(r"\b\d+\b", reply) if 1 <= int(n) <= len(facts)}

    def remember(self, fact: str) -> str:
        fact = " ".join(str(fact).split())
        if not fact:
            raise ValueError("The fact is empty; nothing was saved.")
        with self._lock:
            facts = self.facts()
            if any(f["fact"] == fact for f in facts):
                return f"Already remembered: {fact}"
            gone = self._replaced(fact, facts)
            kept = [f for i, f in enumerate(facts) if i not in gone]
            kept.append({"fact": fact, "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")})
            self._save(kept)
        note = "" if not gone else " It replaces: " + "; ".join(facts[i]["fact"] for i in sorted(gone)) + "."
        return f"Remembered: {fact}.{note}"

    def recall(self, query: str) -> str:
        facts = self.facts()
        if not facts:
            return "Nothing has been remembered yet."
        q = set(_WORD.findall(str(query).lower()))
        hits = [f["fact"] for f in facts if q & set(_WORD.findall(f["fact"].lower()))]
        if not hits:
            return "No remembered fact matches. Everything remembered:\n" + "\n".join(f"- {f['fact']}" for f in facts)
        return "Remembered facts that match:\n" + "\n".join(f"- {h}" for h in hits)

    def prompt_block(self) -> str:
        facts = self.facts()
        if not facts:
            return "## Memory\nNothing is remembered about this user from earlier sessions yet."
        return ("## Memory\nWhat you remember about this user from earlier sessions (use it):\n"
                + "\n".join(f"- {f['fact']}" for f in facts))


MEMORY_GUIDE = (
    "When the user tells you something about themselves that later sessions should know (their team, "
    "location, an id, what they mean by a word, a standing preference), call remember with that fact as a "
    "full sentence. If they correct something they told you, call remember with the corrected fact."
)
