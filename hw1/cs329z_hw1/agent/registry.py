"""Problem 5 (tool_registry), v1 — Ning's design: three functions.

schemas  -> the tools' info
validate -> find the tool, check the arguments
execute  -> run the Python function directly
"""
from __future__ import annotations

from jsonschema import Draft202012Validator

from cs329z_hw1.types import ToolResult, ToolSpec


class ToolRegistry:
    def __init__(self, tools: list[ToolSpec]) -> None:
        self.tools = {t.name: t for t in tools}

    def schemas(self) -> list[dict]:
        return [{"name": t.name, "description": t.description, "parameters": t.parameters}
                for t in self.tools.values()]

    def validate(self, name: str, args: dict) -> ToolResult | None:
        if name not in self.tools:
            return ToolResult("unknown_tool", f"No tool named {name}.")
        errors = list(Draft202012Validator(self.tools[name].parameters).iter_errors(args))
        if errors:
            return ToolResult("invalid_args", "; ".join(e.message for e in errors))
        return None

    def execute(self, name: str, args: dict) -> ToolResult:
        rejected = self.validate(name, args)  # v2: check before running
        if rejected is not None:
            return rejected
        try:  # v3: a tool that raises must not take the agent down
            return ToolResult("ok", str(self.tools[name].fn(**args)))
        except Exception as e:
            return ToolResult("tool_error", f"{name} failed: {e}")
