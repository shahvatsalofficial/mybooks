from __future__ import annotations

import time
from dataclasses import dataclass, field


class BudgetExhaustedError(RuntimeError):
    """Raised when a diagnostic loop exceeds its allocated step, byte, or time budget."""


@dataclass
class DiagnosticBudgetGuard:
    max_tool_calls: int = 12
    max_context_bytes: int = 32_768
    max_wall_seconds: float = 15.0
    tool_calls_used: int = 0
    bytes_accumulated: int = 0
    started_at: float = field(default_factory=time.monotonic)

    def charge_tool_call(self, payload: str) -> None:
        elapsed = time.monotonic() - self.started_at
        if elapsed > self.max_wall_seconds:
            raise BudgetExhaustedError(f"Wall-clock budget exceeded: {elapsed:.2f}s > {self.max_wall_seconds}s")

        self.tool_calls_used += 1
        if self.tool_calls_used > self.max_tool_calls:
            raise BudgetExhaustedError(f"Tool call ceiling reached: {self.tool_calls_used} > {self.max_tool_calls}")

        payload_bytes = len(payload.encode("utf-8"))
        self.bytes_accumulated += payload_bytes
        if self.bytes_accumulated > self.max_context_bytes:
            raise BudgetExhaustedError(
                f"Context byte ceiling reached: {self.bytes_accumulated} > {self.max_context_bytes}"
            )

    def summary(self) -> dict[str, float | int]:
        return {
            "tool_calls_used": self.tool_calls_used,
            "bytes_accumulated": self.bytes_accumulated,
            "elapsed_sec": round(time.monotonic() - self.started_at, 4),
        }


if __name__ == "__main__":
    guard = DiagnosticBudgetGuard(max_tool_calls=5, max_context_bytes=4096, max_wall_seconds=10.0)
    for idx in range(1, 5):
        guard.charge_tool_call(f"pod_event_chunk_{idx}:" + ("x" * 256))
    print("Budget status:", guard.summary())
