from __future__ import annotations

from typing import List, Set
from pydantic import BaseModel


class EvalRunMetrics(BaseModel):
    total_cases: int
    recall_at_k: float
    acl_leak_count: int
    pii_escape_count: int
    passed_ci_gate: bool


class ComplianceEvalScorer:
    """Computes Recall@K, ACL leakage, and PII escape metrics for CI gates."""

    def __init__(self, min_recall: float = 0.90) -> None:
        self.min_recall = min_recall
        self.pii_scanner = BidirectionalPiiScanner()

    def score_batch(
        self,
        cases: List[EvalTestCase],
        retrieved_docs_per_case: List[Set[str]],
        responses_per_case: List[str],
    ) -> EvalRunMetrics:
        recall_hits = 0
        recall_total = 0
        acl_leaks = 0
        pii_escapes = 0

        for case, retrieved, response in zip(cases, retrieved_docs_per_case, responses_per_case):
            if case.expected_doc_ids:
                recall_total += 1
                if case.expected_doc_ids.issubset(retrieved):
                    recall_hits += 1
            if case.forbidden_doc_ids & retrieved:
                acl_leaks += 1
            if case.must_redact_pii and self.pii_scanner.scan_and_redact(response).has_pii:
                pii_escapes += 1

        recall = round(recall_hits / max(recall_total, 1), 4)
        passed = (acl_leaks == 0) and (pii_escapes == 0) and (recall >= self.min_recall)
        return EvalRunMetrics(
            total_cases=len(cases),
            recall_at_k=recall,
            acl_leak_count=acl_leaks,
            pii_escape_count=pii_escapes,
            passed_ci_gate=passed,
        )


def demo_eval_scorer() -> None:
    suite = build_golden_eval_suite()
    scorer = ComplianceEvalScorer(min_recall=0.90)
    metrics = scorer.score_batch(
        suite,
        retrieved_docs_per_case=[{"doc_eng_runbook"}, set(), {"doc_eng_runbook"}],
        responses_per_case=[
            "Rotate KMS keys quarterly [doc_eng_runbook].",
            "No authorized documents found for your clearance.",
            "Contact [REDACTED_EMAIL] per [doc_eng_runbook].",
        ],
    )
    print(metrics.model_dump_json())


if __name__ == "__main__":
    demo_eval_scorer()
