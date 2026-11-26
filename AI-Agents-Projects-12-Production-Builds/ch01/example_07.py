from __future__ import annotations

import math
import re
from collections import Counter


def chunk_with_offsets(doc: SourceDocument, max_chars: int = 320, overlap: int = 40) -> list[EvidenceSpan]:
    text = doc.raw_text
    spans: list[EvidenceSpan] = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        quote = text[start:end].strip()
        if len(quote) >= 15:
            spans.append(
                EvidenceSpan(
                    span_id=f"{doc.doc_id}_s{idx}",
                    doc_id=doc.doc_id,
                    url=doc.url,
                    start_char=start,
                    end_char=end,
                    exact_quote=quote,
                )
            )
            idx += 1
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return spans


def rank_spans_bm25_trust(
    query: str,
    spans: list[EvidenceSpan],
    doc_trust_map: dict[str, float],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[tuple[EvidenceSpan, float]]:
    tokenize = lambda s: re.findall(r"[a-z0-9]+", s.lower())
    q_terms = tokenize(query)
    tokenized_docs = [tokenize(sp.exact_quote) for sp in spans]
    avg_dl = sum(len(td) for td in tokenized_docs) / max(1, len(tokenized_docs))
    n_docs = len(spans)

    df: Counter[str] = Counter()
    for td in tokenized_docs:
        for term in set(td):
            df[term] += 1

    scored: list[tuple[EvidenceSpan, float]] = []
    raw_bm25: list[float] = []
    for sp, td in zip(spans, tokenized_docs):
        tf = Counter(td)
        dl = len(td)
        score = 0.0
        for qt in q_terms:
            if qt not in tf:
                continue
            idf = math.log(1.0 + (n_docs - df[qt] + 0.5) / (df[qt] + 0.5))
            num = tf[qt] * (k1 + 1.0)
            den = tf[qt] + k1 * (1.0 - b + b * (dl / max(1.0, avg_dl)))
            score += idf * (num / den)
        raw_bm25.append(score)

    max_bm25 = max(raw_bm25) if raw_bm25 and max(raw_bm25) > 0 else 1.0
    for sp, bm in zip(spans, raw_bm25):
        norm_bm = bm / max_bm25
        trust = doc_trust_map.get(sp.doc_id, 0.5)
        final_score = round((0.65 * norm_bm) + (0.35 * trust), 4)
        scored.append((sp, final_score))

    return sorted(scored, key=lambda item: item[1], reverse=True)


if __name__ == "__main__":
    d_nist = SourceDocument(
        doc_id="d_nist",
        url="https://csrc.nist.gov/fips-203",
        domain="csrc.nist.gov",
        title="NIST",
        raw_text="ML-KEM-768 provides NIST security category 3 with 1184-byte encapsulation keys and 1088-byte ciphertexts.",
        trust_score=0.96,
    )
    d_blog = SourceDocument(
        doc_id="d_blog",
        url="https://blog.example.com/pqc",
        domain="blog.example.com",
        title="Blog",
        raw_text="Quantum computers might threaten RSA-2048 within the next decade, prompting industry migration discussions.",
        trust_score=0.50,
    )
    all_spans = chunk_with_offsets(d_nist) + chunk_with_offsets(d_blog)
    ranked = rank_spans_bm25_trust(
        "ML-KEM-768 encapsulation key size",
        all_spans,
        {"d_nist": 0.96, "d_blog": 0.50},
    )
    for sp, sc in ranked:
        print(f"span={sp.span_id} score={sc:.4f} quote='{sp.exact_quote[:68]}...'")
