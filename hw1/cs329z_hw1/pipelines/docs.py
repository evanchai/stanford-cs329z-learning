"""Problem 9 (search_docs), v1 — Ning's design: one chunk size for everything.

Each document is cut into chunks of whole lines, at most CHUNK_TOKENS tokens each
(lines are packed in order until the next one would not fit). BM25 runs over the
chunks; a search result's snippet IS the matching chunk; a read window is one chunk's
worth of lines from start_line on.
"""
from __future__ import annotations

import re

from cs329z_hw1.pipelines.bm25 import BM25Index
from cs329z_hw1.tokens import count_tokens

CHUNK_TOKENS = 150   # search unit and snippet (the test caps snippets at 150)
WINDOW_TOKENS = 600  # v2 (Ning): read_doc window, 150 * 4


def _window(lines: list[str], start: int, limit: int = CHUNK_TOKENS) -> int:
    """Index (exclusive) of the last line that fits in ``limit`` tokens starting at ``start`` (0-based)."""
    end, used = start, 0
    while end < len(lines):
        cost = count_tokens("\n".join(lines[start:end + 1]))
        if cost > limit and end > start:
            break
        used = cost
        end += 1
        if used >= limit:
            break
    return end


_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)")
_DATE = re.compile(r"\b(20\d\d-\d\d-\d\d)\b")


def _sections(lines: list[str]) -> list[str]:
    """For each line, the heading path it sits under, e.g. "5. Carryover" or "Benefits > Gym"."""
    path: list[tuple[int, str]] = []
    out = []
    for line in lines:
        m = _HEADING.match(line)
        if m:
            level = len(m.group(1))
            path = [p for p in path if p[0] < level] + [(level, m.group(2))]
        out.append(" > ".join(t for lvl, t in path if lvl > 1) or "(top)")
    return out


class DocIndex:
    """v3: chunks start at section headings and know their section (#2); every
    document carries the date found in its header lines (#3)."""

    def __init__(self, docs: list[dict]) -> None:
        self.docs = {d["doc_id"]: d for d in docs}
        self.lines = {d["doc_id"]: d["text"].splitlines() for d in docs}
        self.section = {d["doc_id"]: _sections(self.lines[d["doc_id"]]) for d in docs}
        self.date = {}
        for d in docs:
            m = _DATE.search("\n".join(self.lines[d["doc_id"]][:12]))
            self.date[d["doc_id"]] = m.group(1) if m else "undated"
        self.chunks: list[tuple[str, int, int]] = []  # (doc_id, first line, last line), 1-based
        for d in docs:
            lines, i = self.lines[d["doc_id"]], 0
            while i < len(lines):
                j = _window(lines, i)
                for h in range(i + 1, j):  # a new section starts a new chunk
                    if _HEADING.match(lines[h]):
                        j = h
                        break
                self.chunks.append((d["doc_id"], i + 1, j))
                i = j
        # what BM25 sees: title and section path, then the chunk itself
        self.bm25 = BM25Index([f"{self.docs[c[0]]['title']}\n{self.section[c[0]][c[1] - 1]}\n{self.text(*c)}"
                               for c in self.chunks])

    def text(self, doc_id: str, first: int, last: int) -> str:
        return "\n".join(self.lines[doc_id][first - 1:last])

    def search(self, query: str, k: int = 10) -> list[dict]:
        out = []
        for i, _ in self.bm25.search(query, k):
            doc_id, first, last = self.chunks[i]
            out.append({"doc_id": doc_id, "title": self.docs[doc_id]["title"], "snippet": self.text(doc_id, first, last),
                        "start_line": first, "end_line": last, "total_lines": len(self.lines[doc_id]),
                        "section": self.section[doc_id][first - 1], "date": self.date[doc_id]})
        return out

    def read(self, doc_id: str, start_line: int = 1) -> dict:
        if doc_id not in self.docs:
            raise LookupError(f"No document with doc_id {doc_id!r}.")
        lines = self.lines[doc_id]
        if not isinstance(start_line, int) or not 1 <= start_line <= len(lines):
            raise ValueError(f"start_line must be between 1 and {len(lines)} for {doc_id}.")
        end = _window(lines, start_line - 1, WINDOW_TOKENS)
        return {"doc_id": doc_id, "start_line": start_line, "end_line": end,
                "total_lines": len(lines), "text": self.text(doc_id, start_line, end),
                "section": self.section[doc_id][start_line - 1], "date": self.date[doc_id]}
