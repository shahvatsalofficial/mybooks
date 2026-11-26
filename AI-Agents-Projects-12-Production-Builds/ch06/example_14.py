from __future__ import annotations

from enum import Enum


class ReplyIntent(str, Enum):
    UNSUBSCRIBE = "unsubscribe"
    OUT_OF_OFFICE = "out_of_office"
    POSITIVE_BOOKING = "positive_booking"
    OBJECTION = "objection"


def classify_reply_intent(reply_text: str) -> tuple[ReplyIntent, bool]:
    text = reply_text.lower()
    if any(k in text for k in ("unsubscribe", "remove me", "stop emailing", "opt out")):
        return ReplyIntent.UNSUBSCRIBE, True
    if any(k in text for k in ("out of office", "ooo", "returning on", "away from my desk")):
        return ReplyIntent.OUT_OF_OFFICE, False
    if any(k in text for k in ("happy to chat", "send calendar", "tuesday works", "book a demo")):
        return ReplyIntent.POSITIVE_BOOKING, True
    return ReplyIntent.OBJECTION, True


if __name__ == "__main__":
    replies = [
        "Thanks, Tuesday works for a 20-minute architecture walkthrough.",
        "I am out of office returning on Dec 2.",
        "Please remove me from your mailing list.",
    ]
    for msg in replies:
        intent, halt_seq = classify_reply_intent(msg)
        print(f"intent={intent.value:18s} halt_sequence={halt_seq}")
