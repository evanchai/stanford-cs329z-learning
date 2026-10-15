"""Problem 6 (tool_protocol), v1 — Ning's design.

The rendered tools go at the top of the prompt. The model's whole reply is one JSON
object saying whether to call a tool, which one, and with which params (plus "text"
for anything it says, which is the final answer when no tool is called).
"""
from __future__ import annotations

import json
import re

from cs329z_hw1.types import ParsedResponse, ToolCall


def render_tools(schemas: list[dict]) -> str:
    lines = ["# Tools", ""]
    for s in schemas:
        lines.append(f"## {s['name']}")
        lines.append(s.get("description", ""))
        lines.append("Parameters (JSON Schema): " + json.dumps(s.get("parameters", {})))
        lines.append("")
    lines += [
        "# How to reply",
        "Reply with one JSON object and nothing else: no code fences (```), no text before or after it.",
        "This JSON is the only way to call a tool here. Do not use <invoke>, <function_calls> or any other tool syntax.",
        '{"use_tool": true, "tool_name": "<tool name>", "params": {<arguments>}, "text": "<optional note>"}',
        "or, when you do not need a tool:",
        '{"use_tool": false, "text": "<your answer>"}',
    ]
    return "\n".join(lines)


def format_tool_call(text: str, call: ToolCall) -> str:
    return json.dumps({"use_tool": True, "tool_name": call.name, "params": call.args, "text": text})


_DECODER = json.JSONDecoder()
# v3: a tool call written in another syntax (e.g. the model's native <invoke name="...">) is not a final
# answer: it is reported as an error so the model rewrites it in JSON.
_FOREIGN_CALL = re.compile(r"<\s*/?\s*(invoke|function_calls|tool_use|tool_call|parameter)", re.I)  # also <invoke_placeholder>


def _first_object(text: str, start: int = 0):
    """(object, end index) of the first JSON object at or after ``start``, or (None, -1)."""
    i = text.find("{", start)
    while i != -1:
        try:
            obj, end = _DECODER.raw_decode(text, i)
            if isinstance(obj, dict):
                return obj, end
        except json.JSONDecodeError:
            pass
        i = text.find("{", i + 1)
    return None, -1


def _clean(s: str) -> str:
    return s.replace("```json", "").replace("```", "").strip()


def parse_response(text: str) -> ParsedResponse:
    """v2: read the first JSON object in the reply, so a code fence or a sentence around it
    does not break parsing (prompt also asks for bare JSON). Text with no JSON object is a
    final answer; an unfinished call (it mentions "use_tool" but no object parses) is an
    error; a second call after the first is an error."""
    if not isinstance(text, str):
        text = str(text)
    obj, end = _first_object(text)
    if obj is None:
        if _FOREIGN_CALL.search(text):
            return ParsedResponse(text="", error=(
                "You wrote a tool call in a format this system does not run (like <invoke ...>), so nothing ran. "
                'Write it again as one JSON object: {"use_tool": true, "tool_name": "...", "params": {...}}'))
        if '"use_tool"' in text:
            return ParsedResponse(text="", error="The tool call is not valid JSON (it may have been cut off). Write it again.")
        return ParsedResponse(text=_clean(text))
    start = text.find("{")
    outside = _clean(text[:start] + " " + text[end:])
    second, _ = _first_object(text, end)
    if second is not None and second.get("use_tool"):
        return ParsedResponse(text=outside, error="The reply contains more than one tool call. Call one tool per reply.")
    note = str(obj.get("text") or "").strip() or outside
    if not obj.get("use_tool"):
        return ParsedResponse(text=note)
    name, params = obj.get("tool_name"), obj.get("params", {})
    if not isinstance(name, str) or not isinstance(params, dict):
        return ParsedResponse(text=note, error='"tool_name" must be a string and "params" an object.')
    return ParsedResponse(text=note, tool_call=ToolCall(name, params))
