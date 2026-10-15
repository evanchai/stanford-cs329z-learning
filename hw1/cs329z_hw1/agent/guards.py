"""Problem 14 (guardrails), v1 — Ning chose checks A + B around run_terminal, on top of the deny rules.

A "copied from data": a command that appears word for word in something a tool returned (a
  document, an email, a search result) is not run. People do not ask the agent to run commands
  found inside documents; text that tells "AI assistants" to run something does.
B "auto mode only reads": in auto mode, commands that create, change or delete files are not run
  (touch, mkdir, rm, mv, cp, tee, sed -i, shell redirection >, Python file writes or deletes).
"""
from __future__ import annotations

import re

_WRITE_PROGRAMS = re.compile(r"(^|[;&|(\s])(touch|mkdir|rmdir|rm|mv|cp|tee|ln|chmod|chown|truncate|dd|install)\b")
_SED_INPLACE = re.compile(r"\bsed\b[^|;&]*\s-i")
_PY_WRITE = re.compile(
    r"open\([^)]*['\"](w|a|x|r\+|w\+|a\+|wb|ab)['\"]|\.write_(text|bytes)\(|os\.(remove|unlink|rmdir|makedirs|mkdir|rename|replace)\("
    r"|shutil\.(rmtree|move|copy|copyfile|copytree)\(|\.unlink\(|\.mkdir\(|\.rename\(")
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")


def _norm(s: str) -> str:
    return " ".join(s.split())


def copied_from_data(cmd: str, tool_texts: list[str]) -> bool:
    """Check A."""
    c = _norm(cmd).strip("`").strip()
    if len(c) < 8:
        return False
    return any(c in _norm(t) for t in tool_texts)


def writes_files(cmd: str) -> bool:
    """Check B."""
    if _WRITE_PROGRAMS.search(cmd) or _SED_INPLACE.search(cmd) or _PY_WRITE.search(cmd):
        return True
    shell = _QUOTED.sub(" ", cmd)  # redirection only counts outside quotes (Python code uses > too)
    shell = re.sub(r"\d?>\s*/dev/null|2>&1", " ", shell)
    return ">" in shell
