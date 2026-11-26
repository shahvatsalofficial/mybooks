from __future__ import annotations


def render_grounded_report(
    objective: str,
    verified_claims: list[AtomicClaim],
    span_lookup: dict[str, EvidenceSpan],
    conflicts: list[ConflictReport],
) -> str:
    url_to_index: dict[str, int] = {}
    ordered_urls: list[str] = []

    def register_url(url_str: str) -> int:
        if url_str not in url_to_index:
            ordered_urls.append(url_str)
            url_to_index[url_str] = len(ordered_urls)
        return url_to_index[url_str]

    lines: list[str] = [f"# Intelligence Brief: {objective}", "", "## Verified Findings", ""]
    for claim in verified_claims:
        if not claim.verified:
            continue
        cite_nums: list[int] = []
        for sid in claim.supporting_span_ids:
            sp = span_lookup.get(sid)
            if sp:
                cite_nums.append(register_url(str(sp.url)))
        cites_str = "".join(f"[{n}]" for n in sorted(set(cite_nums)))
        lines.append(f"- {claim.statement} {cites_str} (entailment={claim.entailment_score:.2f})")

    if conflicts:
        lines.extend(["", "## Source Discrepancies Requiring Review", ""])
        for cf in conflicts:
            lines.append(
                f"- Conflict between `{cf.claim_a_id}` ({sorted(cf.values_a)}) "
                f"and `{cf.claim_b_id}` ({sorted(cf.values_b)})"
            )

    lines.extend(["", "## References", ""])
    for idx, url in enumerate(ordered_urls, start=1):
        lines.append(f"[{idx}] {url}")

    return "\n".join(lines)


if __name__ == "__main__":
    sp1 = EvidenceSpan(
        span_id="s1",
        doc_id="d1",
        url="https://csrc.nist.gov/fips-203",
        start_char=0,
        end_char=80,
        exact_quote="ML-KEM-768 uses 1184-byte encapsulation keys.",
    )
    claims = [
        AtomicClaim(
            claim_id="c1",
            statement="ML-KEM-768 uses 1184-byte encapsulation keys.",
            supporting_span_ids=["s1"],
            entailment_score=0.98,
            verified=True,
        ),
        AtomicClaim(
            claim_id="c_drop",
            statement="Unverified rumor claim.",
            supporting_span_ids=["s1"],
            entailment_score=0.22,
            verified=False,
        ),
    ]
    report = render_grounded_report("PQC Migration", claims, {"s1": sp1}, [])
    print(report)
