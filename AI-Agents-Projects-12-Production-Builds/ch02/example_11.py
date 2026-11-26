from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FailureDiagnostic:
    test_name: str
    file_line: str
    error_summary: str


FAILED_HEADER_RE = re.compile(r"^FAILED\s+([^\s]+)\s+-\s+(.+)$", re.MULTILINE)
FILE_LINE_RE = re.compile(r"([A-Za-z0-9_./\\-]+\.py:\d+):")


def parse_pytest_failures(raw_output: str) -> list[FailureDiagnostic]:
    diagnostics: list[FailureDiagnostic] = []
    line_matches = FILE_LINE_RE.findall(raw_output)
    last_loc = line_matches[-1] if line_matches else "unknown:0"

    for test_id, reason in FAILED_HEADER_RE.findall(raw_output):
        diagnostics.append(
            FailureDiagnostic(
                test_name=test_id,
                file_line=last_loc,
                error_summary=reason.strip(),
            )
        )
    return diagnostics


if __name__ == "__main__":
    sample_tb = """
billing/fees.py:14: AssertionError
FAILED tests/test_fees.py::test_compute_fee_negative - AssertionError: assert -2.5 == 0
"""
    diags = parse_pytest_failures(sample_tb)
    for d in diags:
        print(f"test={d.test_name} loc={d.file_line} err='{d.error_summary}'")
