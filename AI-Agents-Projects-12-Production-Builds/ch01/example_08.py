from __future__ import annotations


def estimate_tokens(text: str) -> int:
    # Fast deterministic approximation: ~3.7 chars per token for technical English
    return max(1, (len(text) + 3) // 4)


def pack_evidence_budget(
    ranked_spans: list[tuple[EvidenceSpan, float]],
    max_tokens: int = 1200,
    max_spans_per_doc: int = 2,
) -> tuple[list[EvidenceSpan], int]:
    selected: list[EvidenceSpan] = []
    doc_counts: dict[str, int] = {}
    used_tokens = 0

    for span, _score in ranked_spans:
        if doc_counts.get(span.doc_id, 0) >= max_spans_per_doc:
            continue
        cost = estimate_tokens(span.exact_quote) + 28  # Header overhead for [span_id | url]
        if used_tokens + cost > max_tokens:
            continue
        selected.append(span)
        doc_counts[span.doc_id] = doc_counts.get(span.doc_id, 0) + 1
        used_tokens += cost

    return selected, used_tokens


if __name__ == "__main__":
    sample_ranked = [
        (
            EvidenceSpan(
                span_id=f"d{i // 3}_s{i}",
                doc_id=f"d{i // 3}",
                url=f"https://example.org/doc/{i // 3}",
                start_char=0,
                end_char=120,
                exact_quote=f"Empirical benchmark #{i}: throughput reached {1200 + i * 40} req/s at p99 18ms.",
            ),
            round(0.95 - i * 0.04, 2),
        )
        for i in range(9)
    ]
    packed, tokens = pack_evidence_budget(sample_ranked, max_tokens=220, max_spans_per_doc=2)
    print(f"Packed {len(packed)} spans using {tokens}/220 tokens:")
    for p in packed:
        print(f"  [{p.span_id}] doc={p.doc_id}")
