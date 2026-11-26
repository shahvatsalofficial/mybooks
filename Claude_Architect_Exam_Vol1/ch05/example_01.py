from __future__ import annotations
import json
import re
from dataclasses import dataclass
from typing import Any, Callable


MAX_ACTIVE_TOOLS = 18
INVOICE_RE = re.compile(r"^INV-[0-9]{5}$")


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class ScopedToolRegistry:
    def __init__(self, max_tools: int = MAX_ACTIVE_TOOLS) -> None:
        self._max_tools = max_tools
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if len(self._tools) >= self._max_tools:
            raise ValueError(
                f"Tool-scaling cliff guard: cannot exceed {self._max_tools} active tools."
            )
        self._tools[spec.name] = spec

    def dispatch(self, tool_use_id: str, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            return self._error_block(
                tool_use_id,
                "UNKNOWN_TOOL",
                f"Tool '{name}' is not in the active triage toolset.",
                f"Choose one of: {sorted(self._tools.keys())}",
            )
        try:
            payload = self._tools[name].handler(args)
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "is_error": False,
                "content": json.dumps(payload),
            }
        except ValueError as exc:
            return self._error_block(
                tool_use_id,
                "VALIDATION_ERROR",
                str(exc),
                "Fix the invalid field and retry the tool call.",
            )

    @staticmethod
    def _error_block(
        tool_use_id: str, code: str, message: str, hint: str
    ) -> dict[str, Any]:
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "is_error": True,
            "content": json.dumps({"error_code": code, "message": message, "recovery_hint": hint}),
        }


def get_invoice(args: dict[str, Any]) -> dict[str, Any]:
    invoice_id = str(args.get("invoice_id", ""))
    if not INVOICE_RE.match(invoice_id):
        raise ValueError(
            f"Invalid invoice_id '{invoice_id}'. Expected pattern ^INV-[0-9]{{5}}$ (e.g., INV-88412)."
        )
    return {"invoice_id": invoice_id, "amount_usd": 49.00, "status": "duplicate_detected"}


def main() -> None:
    registry = ScopedToolRegistry()
    registry.register(
        ToolSpec(
            name="billing_get_invoice",
            description="[READ-ONLY] Fetch invoice totals and duplicate-charge flags by ID.",
            input_schema={
                "type": "object",
                "properties": {"invoice_id": {"type": "string", "pattern": "^INV-[0-9]{5}$"}},
                "required": ["invoice_id"],
            },
            handler=get_invoice,
        )
    )

    turn_1 = registry.dispatch("tu_01", "billing_get_invoice", {"invoice_id": "88412"})
    print("Turn 1 (malformed):", json.dumps(turn_1))

    turn_2 = registry.dispatch("tu_02", "billing_get_invoice", {"invoice_id": "INV-88412"})
    print("Turn 2 (corrected):", json.dumps(turn_2))


if __name__ == "__main__":
    main()
