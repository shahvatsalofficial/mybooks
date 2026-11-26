from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineMetrics:
    total_ms: float
    waves_executed: int
    raw_docs: int
    surviving_docs: int
    packed_spans: int
    claims_verified: int
    claims_quarantined: int


async def run_research_pipeline(objective: str) -> tuple[str, PipelineMetrics]:
    t0 = time.perf_counter()
    planner = HeuristicFallbackPlanner()
    dag = await planner.generate_dag(objective)
    waves = build_execution_waves(dag)

    # Simulated wave execution returning canonical SourceDocuments
    raw_docs: list[SourceDocument] = []
    for w_idx, wave in enumerate(waves):
        await asyncio.sleep(0.02)
        for node in wave:
            raw_docs.append(
                SourceDocument(
                    doc_id=f"doc_w{w_idx}_{node.node_id}",
                    url=f"https://docs.example.org/{node.node_id}",
                    domain="docs.example.org",
                    title=f"Report for {node.node_id}",
                    raw_text=(
                        f"Official benchmark for {node.node_id}: throughput 1,480 tokens/sec "
                        "with 99.4% citation fidelity under strict NLI gating."
                    ),
                    tier=SourceTier.PRIMARY_OFFICIAL,
                    trust_score=0.92,
                )
            )
    # Inject one duplicate to exercise dedup
    raw_docs.append(
        SourceDocument(
            doc_id="doc_dup_copy",
            url="https://mirror.example.net/copy",
            domain="mirror.example.net",
            title="Mirror Copy",
            raw_text=raw_docs[0].raw_text,
            tier=SourceTier.NEWS_AGGREGATOR,
            trust_score=0.41,
        )
    )

    embs = {d.doc_id: [0.5, 0.5, 0.5] for d in raw_docs}
    embs[raw_docs[0].doc_id] = [0.9, 0.1, 0.1]
    embs["doc_dup_copy"] = [0.9, 0.1, 0.1]
    for idx, d in enumerate(raw_docs[1:-1], start=1):
        embs[d.doc_id] = [0.1 * idx, 0.8, 0.2 * idx]

    clean_docs, dedup_stats = deduplicate_documents(raw_docs, embs)
    all_spans = [sp for d in clean_docs for sp in chunk_with_offsets(d)]
    trust_map = {d.doc_id: d.trust_score for d in clean_docs}
    ranked = rank_spans_bm25_trust(objective, all_spans, trust_map)
    packed, _ = pack_evidence_budget(ranked, max_tokens=1500)
    span_lookup = {sp.span_id: sp for sp in packed}

    candidate_claims = [
        AtomicClaim(
            claim_id=f"claim_{i}",
            statement="Official benchmark throughput reached 1,480 tokens/sec with 99.4% citation fidelity.",
            supporting_span_ids=[packed[0].span_id],
        )
        for i in range(1)
    ] + [
        AtomicClaim(
            claim_id="claim_bad",
            statement="Official benchmark throughput reached 9,999 tokens/sec.",
            supporting_span_ids=[packed[0].span_id],
        )
    ]

    ref_ok, _ = validate_claim_references(candidate_claims, packed)
    checked = [evaluate_entailment(c, span_lookup) for c in ref_ok]
    verified = [c for c in checked if c.verified]
    quarantined = len(candidate_claims) - len(verified)
    conflicts = detect_numeric_conflicts(verified)
    report = render_grounded_report(objective, verified, span_lookup, conflicts)

    metrics = PipelineMetrics(
        total_ms=round((time.perf_counter() - t0) * 1000, 2),
        waves_executed=len(waves),
        raw_docs=dedup_stats.input_count,
        surviving_docs=dedup_stats.surviving_count,
        packed_spans=len(packed),
        claims_verified=len(verified),
        claims_quarantined=quarantined,
    )
    return report, metrics


if __name__ == "__main__":
    brief, m = asyncio.run(run_research_pipeline("Evaluate NLI-gated synthesis throughput"))
    print(f"PipelineMetrics: {m}")
    print(brief.splitlines()[0])
