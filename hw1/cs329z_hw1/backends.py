"""Run LM calls through a subscription CLI instead of OpenRouter.

Set CS329Z_BACKEND in .env:
    openrouter  (default) the course setup, needs OPENROUTER_API_KEY
    claude      Claude Code CLI, logged in with your Claude subscription (`claude` then /login)
    codex       Codex CLI, logged in with your ChatGPT subscription (`codex login`)

Optional:
    CS329Z_CLI_MODEL   model passed to the CLI (e.g. "sonnet", "opus", "gpt-6-luna")
    CS329Z_CLI_TIMEOUT seconds per call, default 300

Both CLIs are agents, not raw model endpoints. They are run here with tools
disabled and a single turn, so each call is "messages in, text out" like the
course wrapper. They still add their own system prompt, so scores will not
match the grading model; the handout warns prompts do not transfer between
models. Subscription calls have no per-call price, so the ledger records cost 0.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from typing import Sequence

Message = dict


def backend_name() -> str:
    return os.environ.get("CS329Z_BACKEND", "openrouter").strip().lower()


def _split(messages: Sequence[Message]) -> tuple[str, str]:
    """System prompt, and the rest of the conversation rendered as one prompt."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    turns = [m for m in messages if m["role"] != "system"]
    if len(turns) == 1 and turns[0]["role"] == "user":
        return system, turns[0]["content"]
    parts = []
    for m in turns:
        tag = "USER" if m["role"] == "user" else "ASSISTANT"
        parts.append(f"<{tag}>\n{m['content']}\n</{tag}>")
    parts.append("Write the next ASSISTANT turn. Reply with its content only, without the tag.")
    return system, "\n\n".join(parts)


def _need(cli: str) -> str:
    path = shutil.which(cli)
    if not path:
        raise RuntimeError(f"CS329Z_BACKEND={backend_name()} but `{cli}` is not on PATH.")
    return path


def _usage(inp: int = 0, out: int = 0, cached: int = 0) -> dict:
    return {"input": inp, "cached": cached, "output": out, "reasoning": 0,
            "finish_reason": "stop", "cost": 0.0}


def complete_claude(messages: Sequence[Message]) -> tuple[str, dict]:
    system, prompt = _split(messages)
    cmd = [_need("claude"), "-p", "--output-format", "json", "--max-turns", "1", "--tools", "",
           "--strict-mcp-config", "--no-chrome"]  # no built-in, MCP or browser tools: one plain model turn
    if system:
        cmd += ["--system-prompt", system]
    model = os.environ.get("CS329Z_CLI_MODEL")
    if model:
        cmd += ["--model", model]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                       timeout=float(os.environ.get("CS329Z_CLI_TIMEOUT", 300)),
                       cwd=tempfile.gettempdir())  # keep it away from the repo's CLAUDE.md
    if r.returncode != 0:
        raise RuntimeError(f"claude CLI failed ({r.returncode}): {r.stderr.strip()[:500]}")
    data = json.loads(r.stdout)
    if data.get("is_error"):
        raise RuntimeError(f"claude CLI error: {data.get('result')}")
    u = data.get("usage") or {}
    return data.get("result", ""), _usage(
        u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
        u.get("output_tokens", 0),
        u.get("cache_read_input_tokens", 0),
    )


def complete_codex(messages: Sequence[Message]) -> tuple[str, dict]:
    system, prompt = _split(messages)
    if system:  # codex exec has no system-prompt flag; put it first
        prompt = f"<SYSTEM>\n{system}\n</SYSTEM>\n\n{prompt}"
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "last.txt")
        cmd = [_need("codex"), "exec", "--skip-git-repo-check", "--sandbox", "read-only",
               "--color", "never", "-C", tmp, "--output-last-message", out]
        model = os.environ.get("CS329Z_CLI_MODEL")
        if model:
            cmd += ["--model", model]
        cmd.append("-")  # read the prompt from stdin
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                           timeout=float(os.environ.get("CS329Z_CLI_TIMEOUT", 300)))
        if r.returncode != 0:
            raise RuntimeError(f"codex CLI failed ({r.returncode}): {r.stderr.strip()[:500]}")
        text = open(out, encoding="utf-8").read() if os.path.exists(out) else r.stdout
    return text.strip(), _usage()


BACKENDS = {"claude": complete_claude, "codex": complete_codex}
