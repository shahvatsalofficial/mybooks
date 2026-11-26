from __future__ import annotations

import re


NUMERIC_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")


def extract_numbers(text: str) -> set[str]:
    return {m.replace(",", "") for m in NUMERIC_PATTERN.findall(text)}


def evaluate_entailment(
    claim: AtomicClaim,
    span_lookup: dict[str, EvidenceSpan],
    min_entailment: float = 0.82,
) -> AtomicClaim:
    combined_evidence = " ".join(
        span_lookup[sid].exact_quote for sid in claim.supporting_span_ids if sid in span_lookup
    )
    claim_nums = extract_numbers(claim.statement)
    evid_nums = extract_numbers(combined_evidence)

    # Hard numeric fidelity gate: any fabricated number drops entailment to 0.10
    if not claim_nums.issubset(evid_nums):
        missing_nums = claim_nums - evid_nums
        return claim.model_copy(
            update={
                "entailment_score": 0.10,
                "verified": False,
            }
        )

    # Content-word overlap proxy (replace with cross-encoder NLI logits in GPU tier)
    stopwords = {"the", "and", "with", "for", "that", "this", "uses", "from", "into"}
    c_words = {w for w in re.findall(r"[a-z0-9-]+", claim.statement.lower()) if len(w) > 2 and w not in stopwords}
    e_words = {w for w in re.findall(r"[a-z0-9-]+", combined_evidence.lower()) if len(w) > 2 and w not in stopwords}

    if not c_words:
        score = 0.0
    else:
        score = round(len(c_words & e_words) / len(c_words), 4)

    return claim.model_copy(
        update={
            "entailment_score": score,
            "verified": score >= min_entailment,
        }
    )


if __name__ == "__main__":
    lookup = {
        "sp1": EvidenceSpan(
            span_id="sp1",
            doc_id="d1",
            url="https://docs.example-zk.org/2026",
            start_char=0,
            end_char=85,
            exact_quote="The Groth16 on-chain verifier consumes 218,400 gas per batch proof on mainnet.",
        )
    }
    c_good = AtomicClaim(
        claim_id="c_good",
        statement="Groth16 on-chain verifier consumes 218,400 gas per batch proof on mainnet.",
        supporting_span_ids=["sp1"],
    )
    c_bad_num = AtomicClaim(
        claim_id="c_bad_num",
        statement="Groth16 on-chain verifier consumes 281,400 gas per batch proof on mainnet.",
        supporting_span_ids=["sp1"],
    )
    for c in (c_good, c_bad_num):
        res = evaluate_entailment(c, lookup)
        print(f"claim={res.claim_id} entailment={res.entailment_score:.4f} verified={res.verified}")
