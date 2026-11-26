from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class PatchResult:
    applied: bool
    new_source: str
    error_reason: str = ""


def apply_guarded_edit(
    original_source: str,
    edit: SearchReplaceEdit,
    expected_span: SymbolSpan | None = None,
) -> PatchResult:
    occurrences = original_source.count(edit.search_block)
    if occurrences == 0:
        return PatchResult(applied=False, new_source=original_source, error_reason="search_block not found")
    if occurrences > 1:
        return PatchResult(
            applied=False,
            new_source=original_source,
            error_reason=f"ambiguous search_block matched {occurrences} times",
        )

    idx = original_source.index(edit.search_block)
    match_start_line = original_source[:idx].count("\n") + 1
    match_end_line = match_start_line + edit.search_block.count("\n")

    if expected_span is not None:
        if match_start_line < expected_span.start_line or match_end_line > expected_span.end_line:
            return PatchResult(
                applied=False,
                new_source=original_source,
                error_reason=(
                    f"edit lines {match_start_line}-{match_end_line} outside symbol "
                    f"{expected_span.name} ({expected_span.start_line}-{expected_span.end_line})"
                ),
            )

    candidate = original_source.replace(edit.search_block, edit.replace_block, 1)
    try:
        ast.parse(candidate, filename=edit.file_path)
    except SyntaxError as exc:
        return PatchResult(
            applied=False,
            new_source=original_source,
            error_reason=f"post-patch SyntaxError at line {exc.lineno}: {exc.msg}",
        )

    return PatchResult(applied=True, new_source=candidate)


if __name__ == "__main__":
    src = (
        "def compute_fee(amount: int) -> float:\n"
        "    return round(amount * 0.025, 2)\n"
    )
    span = index_python_source("billing.fees", "billing/fees.py", src)[0]
    good_edit = SearchReplaceEdit(
        edit_id="e1",
        file_path="billing/fees.py",
        target_symbol="compute_fee",
        search_block="    return round(amount * 0.025, 2)",
        replace_block="    if amount < 0:\n        raise ValueError('amount must be non-negative')\n    return round(amount * 0.025, 2)",
        rationale="Guard against negative settlement amounts.",
    )
    bad_syntax_edit = SearchReplaceEdit(
        edit_id="e2",
        file_path="billing/fees.py",
        target_symbol="compute_fee",
        search_block="    return round(amount * 0.025, 2)",
        replace_block="    return round(amount * 0.025, 2",
        rationale="Broken parenthesis test.",
    )
    r1 = apply_guarded_edit(src, good_edit, span)
    r2 = apply_guarded_edit(src, bad_syntax_edit, span)
    print(f"Edit e1: applied={r1.applied} lines={len(r1.new_source.splitlines())}")
    print(f"Edit e2: applied={r2.applied} error='{r2.error_reason}'")
