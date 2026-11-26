from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    expected_facts: list[str]
    forbidden_tokens: list[str]


def score_eval_case(report_text: str, case: EvalCase) -> dict[str, float | bool]:
    lower = report_text.lower()
    hits = sum(1 for f in case.expected_facts if f.lower() in lower)
    recall = hits / max(1, len(case.expected_facts))
    fabrications = sum(1 for bad in case.forbidden_tokens if bad.lower() in lower)
    return {
        "recall": round(recall, 4),
        "fabrications": fabrications,
        "passed": recall >= 0.80 and fabrications == 0,
    }


if __name__ == "__main__":
    sample_report = (
        "ML-KEM-768 uses 1184-byte encapsulation keys [1]. "
        "Groth16 verifier consumes 218,400 gas [2]."
    )
    cases = [
        EvalCase(
            case_id="pqc_01",
            expected_facts=["1184-byte", "218,400 gas"],
            forbidden_tokens=["EBA-2025-884-REV", "9,999"],
        )
    ]
    for c in cases:
        res = score_eval_case(sample_report, c)
        print(f"Case={c.case_id} recall={res['recall']} fabrications={res['fabrications']} passed={res['passed']}")
