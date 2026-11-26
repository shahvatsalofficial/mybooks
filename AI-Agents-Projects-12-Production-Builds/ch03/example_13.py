from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class HumanResponder(BaseModel):
    responder_id: str
    name: str
    skills: List[str]
    active_tickets: int
    max_capacity: int
    online: bool


class WarmTransferRouter:
    """Assigns escalation packets to the best-matched available human specialist."""

    @staticmethod
    def assign(required_skill: str, responders: List[HumanResponder]) -> Optional[HumanResponder]:
        eligible = [
            r
            for r in responders
            if r.online and required_skill in r.skills and r.active_tickets < r.max_capacity
        ]
        if not eligible:
            return None
        return min(eligible, key=lambda r: r.active_tickets)


if __name__ == "__main__":
    roster = [
        HumanResponder(
            responder_id="eng_101",
            name="Priya Nair",
            skills=["tech_ops", "kubernetes"],
            active_tickets=2,
            max_capacity=5,
            online=True,
        ),
        HumanResponder(
            responder_id="eng_102",
            name="Marcus Vance",
            skills=["tech_ops", "payments"],
            active_tickets=1,
            max_capacity=5,
            online=True,
        ),
    ]
    chosen = WarmTransferRouter.assign("tech_ops", roster)
    print("Assigned responder:", chosen.model_dump() if chosen else "FALLBACK_ONCALL_PAGER")
