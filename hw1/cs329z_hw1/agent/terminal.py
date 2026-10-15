"""Problem 10 (terminal), v1 — Ning's observation policy (option C):
the model sees exit code, stdout and stderr; output too long for the context is cut to
its head and tail, and the full text is saved in the workspace with its path given to
the model, so it can grep / sed the rest on demand (Claude Code / OpenHands style).
"""
from __future__ import annotations

import itertools
from pathlib import Path

from cs329z_hw1 import sandbox
from cs329z_hw1.tokens import CHARS_PER_TOKEN

SHOW_SHARE = 0.25  # the shown output may use at most this share of the context budget

DESCRIPTION = (
    "Run one shell command in a sandboxed workspace and get its exit code, stdout and stderr. "
    "The workspace holds emails.jsonl (the 2001 email archive, one JSON object per line with keys "
    "id, thread_id, reply_to, from, to, date, subject, body; date is ISO 8601 UTC like 2001-07-04T16:56:37Z) "
    "and docs/ (the Cardinal Energy documents as Markdown). Use it to count, filter or compute over the data. "
    "Allowed: python3, grep, wc, sort, uniq, cut, sed, awk, head, tail, jq and similar text tools. "
    "Write multi-line Python as python3 -c '...' in single quotes; here-documents (<<), $(...) and "
    "backticks are rejected. Commands time out after a few seconds. Long output is cut to its start and "
    "end and saved in full to a file whose path the result gives; read the rest with grep -n, sed -n 'A,Bp' "
    "or head/tail on that file."
)


class ToolFailure(Exception):
    """Raised so that the registry reports a tool_error; the message is what the model sees."""


class Terminal:
    def __init__(self, config) -> None:
        self.config = config
        self._n = itertools.count(1)

    def _limit(self) -> int:
        return max(1000, int(self.config.context_budget * CHARS_PER_TOKEN * SHOW_SHARE))

    def _shown(self, name: str, text: str, n: int, limit: int) -> str:
        if len(text) <= limit:
            return text
        rel = Path(".outputs") / f"cmd{n}.{name}.txt"
        ws = Path(self.config.workspace) if self.config.workspace is not None else sandbox.default_workspace()
        note = ""
        try:
            (ws / rel).parent.mkdir(parents=True, exist_ok=True)
            (ws / rel).write_text(text, encoding="utf-8")
            note = (f" Full {name} ({text.count(chr(10)) + (not text.endswith(chr(10)))} lines) saved to {rel}; "
                    f"use grep -n, sed -n 'A,Bp', head or tail on that file to read it.")
        except OSError:
            pass
        head, tail = text[: limit * 3 // 5], text[-(limit * 2 // 5):]
        return f"{head}\n[... {len(text) - len(head) - len(tail):,} of {len(text):,} characters omitted.{note} ...]\n{tail}"

    def __call__(self, cmd: str) -> str:
        n = next(self._n)
        r = sandbox.run_terminal(cmd, workspace=self.config.workspace, timeout=self.config.terminal_timeout)
        if r.rejected:
            raise ToolFailure(f"The sandbox rejected the command and it did not run: {r.reason}")
        limit = self._limit()
        out = self._shown("stdout", r.stdout, n, limit // 2 if r.stderr else limit)
        err = self._shown("stderr", r.stderr, n, limit // 2) if r.stderr else ""
        shown = f"exit code: {r.exit_code}\n--- stdout ---\n{out or '(empty)'}\n--- stderr ---\n{err or '(empty)'}"
        if r.timed_out:
            raise ToolFailure(f"The command timed out after {self.config.terminal_timeout:g} seconds and was killed. "
                              f"{r.reason}\n{shown}")
        if r.exit_code != 0:
            raise ToolFailure(shown)
        return shown
