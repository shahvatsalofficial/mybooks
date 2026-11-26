from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConflictReport:
    topic_key: str
    claim_a_id: str
    claim_b_id: str
    values_a: set[str]
    values_b: set[str]


def detect_numeric_conflicts(claims: list[AtomicClaim]) -> list[ConflictReport]:
    conflicts: list[ConflictReport] = []
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            ca, cb = claims[i], claims[j]
            words_a = set(ca.statement.lower().split())
            words_b = set(cb.statement.lower().split())
            shared = words_a & words_b
            nums_a = extract_numbers(ca.statement)
            nums_b = extract_numbers(cb.statement)
            if len(shared) >= 4 and nums_a and nums_b and nums_a != nums_b:
                conflicts.append(
                    ConflictReport(
                        topic_key=" ".join(sorted(shared)[:4]),
                        claim_a_id=ca.claim_id,
                        claim_b_id=cb.claim_id,
                        values_a=nums_a,
                        values_b=nums_b,
                    )
                )
    return conflicts


if __name__ == "__main__":
    claims = [
        AtomicClaim(
            claim_id="c1",
            statement="Llama-3 70B FP8 inference latency measured 420 ms on single H100.",
            supporting_span_ids=["s1"],
            entailment_score=0.95,
            verified=True,
        ),
        AtomicClaim(
            claim_id="c2",
            statement="Llama-3 70B FP8 inference latency measured 145 ms on single H100.",
            supporting_span_ids=["s2"],
            entailment_score=0.92,
            verified=True,
        ),
    ]
    found = detect_numeric_conflicts(claims)
    print(f"Detected {len(found)} conflict(s):")
    for f in found:
        print(f"  [{f.claim_a_id} vs {f.claim_b_id}] values={f.values_a} vs {f.values_b}")
