from __future__ import annotations

import math
import re
from dataclasses import dataclass


def word_shingles(text: str, k: int = 5) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    if len(tokens) < k:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(x * y for x, y in zip(v1, v2))
    n1 = math.sqrt(sum(x * x for x in v1))
    n2 = math.sqrt(sum(y * y for y in v2))
    if n1 == 0.0 or n2 == 0.0:
        return 0.0
    return dot / (n1 * n2)


@dataclass
class DedupStats:
    input_count: int
    exact_hash_dropped: int
    shingle_dropped: int
    semantic_dropped: int
    surviving_count: int


def deduplicate_documents(
    docs: list[SourceDocument],
    embeddings: dict[str, list[float]],
    shingle_threshold: float = 0.65,
    cosine_threshold: float = 0.88,
) -> tuple[list[SourceDocument], DedupStats]:
    # Sort descending by trust_score so canonical primary sources win every cluster
    ordered = sorted(docs, key=lambda d: d.trust_score, reverse=True)
    seen_hashes: set[str] = set()
    survivors: list[SourceDocument] = []
    survivor_shingles: list[set[str]] = []

    exact_dropped = 0
    shingle_dropped = 0
    semantic_dropped = 0

    for doc in ordered:
        if doc.content_sha256 in seen_hashes:
            exact_dropped += 1
            continue
        seen_hashes.add(doc.content_sha256)

        shingles = word_shingles(doc.raw_text)
        if any(jaccard_similarity(shingles, prev) >= shingle_threshold for prev in survivor_shingles):
            shingle_dropped += 1
            continue

        vec = embeddings.get(doc.doc_id)
        if vec is not None and any(
            cosine_similarity(vec, embeddings[s.doc_id]) >= cosine_threshold
            for s in survivors
            if s.doc_id in embeddings
        ):
            semantic_dropped += 1
            continue

        survivors.append(doc)
        survivor_shingles.append(shingles)

    stats = DedupStats(
        input_count=len(docs),
        exact_hash_dropped=exact_dropped,
        shingle_dropped=shingle_dropped,
        semantic_dropped=semantic_dropped,
        surviving_count=len(survivors),
    )
    return survivors, stats


if __name__ == "__main__":
    base_text = "NIST finalized post-quantum cryptography standards FIPS 203 and FIPS 204 for key encapsulation."
    docs = [
        SourceDocument(
            doc_id="d1",
            url="https://csrc.nist.gov/fips-203",
            domain="csrc.nist.gov",
            title="NIST FIPS 203 Official",
            raw_text=base_text + " Organizations must inventory TLS 1.3 cipher suites immediately.",
            trust_score=0.96,
        ),
        SourceDocument(
            doc_id="d2",
            url="https://mirror.example.com/fips-203",
            domain="mirror.example.com",
            title="Mirror Copy",
            raw_text=base_text + " Organizations must inventory TLS 1.3 cipher suites immediately.",
            trust_score=0.45,
        ),
        SourceDocument(
            doc_id="d3",
            url="https://news.example.com/pqc-summary",
            domain="news.example.com",
            title="News Rewrite",
            raw_text="Post-quantum standards FIPS 203 and 204 were published by NIST for enterprise TLS migration.",
            trust_score=0.52,
        ),
        SourceDocument(
            doc_id="d4",
            url="https://github.com/open-quantum-safe/liboqs",
            domain="github.com",
            title="liboqs Benchmarks",
            raw_text="ML-KEM-768 keygen completes in 24 microseconds on x86_64 AVX2 hardware.",
            trust_score=0.84,
        ),
    ]
    embs = {
        "d1": [0.91, 0.32, 0.10],
        "d2": [0.91, 0.32, 0.10],
        "d3": [0.89, 0.35, 0.11],  # Cosine ~0.999 with d1
        "d4": [0.12, 0.88, 0.45],
    }
    clean, stats = deduplicate_documents(docs, embs)
    print(f"Stats: in={stats.input_count} exact_drop={stats.exact_hash_dropped} "
          f"shingle_drop={stats.shingle_dropped} sem_drop={stats.semantic_dropped} "
          f"survivors={stats.surviving_count}")
    for s in clean:
        print(f"  Kept {s.doc_id} ({s.domain}, trust={s.trust_score})")
