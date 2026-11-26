from __future__ import annotations


def validate_claim_references(
    claims: list[AtomicClaim],
    packed_spans: list[EvidenceSpan],
) -> tuple[list[AtomicClaim], list[str]]:
    valid_ids = {sp.span_id for sp in packed_spans}
    accepted: list[AtomicClaim] = []
    rejected_reasons: list[str] = []

    for claim in claims:
        missing = [sid for sid in claim.supporting_span_ids if sid not in valid_ids]
        if missing:
            rejected_reasons.append(
                f"{claim.claim_id}: fabricated span_id(s) {missing}"
            )
            continue
        accepted.append(claim)

    return accepted, rejected_reasons


if __name__ == "__main__":
    spans = [
        EvidenceSpan(
            span_id="d_nist_s0",
            doc_id="d_nist",
            url="https://csrc.nist.gov/fips-203",
            start_char=0,
            end_char=95,
            exact_quote="ML-KEM-768 provides NIST security category 3 with 1184-byte encapsulation keys.",
        )
    ]
    raw_claims = [
        AtomicClaim(
            claim_id="c1",
            statement="ML-KEM-768 targets NIST security category 3 and uses 1184-byte encapsulation keys.",
            supporting_span_ids=["d_nist_s0"],
        ),
        AtomicClaim(
            claim_id="c2",
            statement="Directive EBA-2025-884-REV mandates 14% capital reserves.",
            supporting_span_ids=["d_phantom_s9"],
        ),
    ]
    ok, errs = validate_claim_references(raw_claims, spans)
    print(f"Accepted={len(ok)} Rejected={len(errs)}")
    for e in errs:
        print(f"  QUARANTINED: {e}")
