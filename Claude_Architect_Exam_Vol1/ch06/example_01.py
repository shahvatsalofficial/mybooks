from __future__ import annotations
import json
import random
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class TicketInvariants:
    ticket_id: str
    customer_tier: str
    max_autonomous_credit_usd: float


@dataclass
class ContextManager:
    invariants: TicketInvariants
    static_policy_prompt: str
    keep_recent_turns: int = 2
    history: list[dict[str, str]] = field(default_factory=list)
    rolled_summary: list[str] = field(default_factory=list)

    def add_turn(self, role: str, content: str, summary_note: str | None = None) -> None:
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.keep_recent_turns:
            evicted = self.history.pop(0)
            note = summary_note or f"{evicted['role']}: {evicted['content'][:48]}..."
            self.rolled_summary.append(note)

    def build_request_payload(self, request_timestamp_utc: str) -> dict[str, Any]:
        # Static blocks BEFORE cache_control breakpoint -> 90% input discount on hits
        system_blocks = [
            {
                "type": "text",
                "text": self.static_policy_prompt,
                "cache_control": {"type": "ephemeral"},
            },
            # Dynamic metadata placed AFTER the breakpoint so prefix stays stable
            {
                "type": "text",
                "text": (
                    f"RequestUTC={request_timestamp_utc} | "
                    f"Invariants={json.dumps(self.invariants.__dict__)} | "
                    f"PriorSummary={'; '.join(self.rolled_summary) or 'None'}"
                ),
            },
        ]
        return {"system": system_blocks, "messages": list(self.history)}


def validate_credit_decision(decision: dict[str, Any], inv: TicketInvariants) -> None:
    """Deterministic code gate: never rely on prompt text alone for money caps."""
    amount = float(decision.get("credit_usd", 0))
    if amount <= 0 or amount > inv.max_autonomous_credit_usd:
        raise ValueError(
            f"Policy violation: ${amount:.2f} exceeds cap ${inv.max_autonomous_credit_usd:.2f}."
        )


def call_with_backoff(
    fn: Callable[[], dict[str, Any]],
    max_attempts: int = 4,
    base_delay: float = 0.5,
    cap_delay: float = 8.0,
    rng_seed: int = 42,
) -> dict[str, Any]:
    rng = random.Random(rng_seed)
    retryable = {429, 529}
    for attempt in range(1, max_attempts + 1):
        resp = fn()
        status = int(resp.get("status", 200))
        if status == 200:
            return resp
        if status not in retryable or attempt == max_attempts:
            raise RuntimeError(f"Non-retryable or exhausted status={status}")
        exp_ceiling = min(cap_delay, base_delay * (2 ** (attempt - 1)))
        sleep_s = round(rng.uniform(0.0, exp_ceiling), 3)
        print(f"Attempt {attempt} hit HTTP {status}; backing off {sleep_s}s (full jitter)")
    raise RuntimeError("Unreachable")


def main() -> None:
    inv = TicketInvariants("TKT-10420", "enterprise_sla", 500.0)
    ctx = ContextManager(inv, static_policy_prompt="You are a support triage architect.")
    ctx.add_turn("user", "Duplicate $49 charge on INV-88412.", "User reported $49 duplicate")
    ctx.add_turn("assistant", "Checked INV-88412: duplicate confirmed.", "Confirmed INV-88412")
    ctx.add_turn("user", "Please apply the $49 credit now.")

    payload = ctx.build_request_payload("2026-11-26T09:15:00Z")
    print("Cached prefix blocks:", len(payload["system"]), "Active messages:", len(payload["messages"]))
    print("Dynamic block:", payload["system"][1]["text"])

    validate_credit_decision({"credit_usd": 49.0}, inv)
    print("Deterministic validator: PASSED for $49.00")

    statuses = iter([{"status": 429}, {"status": 529}, {"status": 200, "ok": True}])
    result = call_with_backoff(lambda: next(statuses))
    print("Final API response:", result)


if __name__ == "__main__":
    main()
