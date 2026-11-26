from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class KbChunk(BaseModel):
    doc_id: str
    title: str
    content: str
    similarity: float = Field(ge=0.0, le=1.0)


class GroundedDraft(BaseModel):
    can_auto_reply: bool
    reply_text: str
    cited_doc_ids: List[str]
    top_similarity: float


class KbGroundedResponder:
    """Generates citation-verified support drafts with confidence gating."""

    def __init__(self, min_similarity: float = 0.78) -> None:
        self._min_sim = min_similarity

    def generate(self, query: str, retrieved: List[KbChunk]) -> GroundedDraft:
        qualified = [c for c in retrieved if c.similarity >= self._min_sim]
        if not qualified:
            top = max((c.similarity for c in retrieved), default=0.0)
            return GroundedDraft(
                can_auto_reply=False,
                reply_text="",
                cited_doc_ids=[],
                top_similarity=top,
            )

        best = max(qualified, key=lambda c: c.similarity)
        citations = [c.doc_id for c in qualified[:2]]
        reply = (
            f"Based on our documentation ({', '.join(citations)}), {best.content} "
            "Please let us know if you need help validating your webhook signature."
        )
        return GroundedDraft(
            can_auto_reply=True,
            reply_text=reply,
            cited_doc_ids=citations,
            top_similarity=best.similarity,
        )


if __name__ == "__main__":
    responder = KbGroundedResponder(min_similarity=0.78)
    chunks = [
        KbChunk(
            doc_id="KB-402",
            title="Webhook HMAC-SHA256 Verification",
            content="compute the HMAC-SHA256 digest over the raw request body using your signing secret and compare against the X-Signature-256 header.",
            similarity=0.91,
        )
    ]
    draft = responder.generate("How do I verify webhook signatures?", chunks)
    print(draft.model_dump_json(indent=2))
