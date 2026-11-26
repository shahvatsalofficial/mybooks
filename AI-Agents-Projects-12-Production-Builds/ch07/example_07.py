from __future__ import annotations

import re
from enum import Enum
from pydantic import BaseModel


class SqlErrorCategory(str, Enum):
    UNDEFINED_COLUMN = "undefined_column"
    UNDEFINED_TABLE = "undefined_table"
    GROUPING_ERROR = "grouping_error"
    TYPE_MISMATCH = "type_mismatch"
    SYNTAX_ERROR = "syntax_error"
    TIMEOUT = "statement_timeout"
    UNKNOWN = "unknown"


class ErrorReflectionHint(BaseModel):
    category: SqlErrorCategory
    offending_symbol: str
    repair_instruction: str


class SqlErrorClassifier:
    """Translates raw database engine errors into deterministic repair hints."""

    def classify(self, error_msg: str) -> ErrorReflectionHint:
        col_match = re.search(r'column "([^"]+)" does not exist', error_msg, re.IGNORECASE)
        if col_match:
            sym = col_match.group(1)
            return ErrorReflectionHint(
                category=SqlErrorCategory.UNDEFINED_COLUMN,
                offending_symbol=sym,
                repair_instruction=(
                    f"Column '{sym}' does not exist. Inspect the provided DDL strictly "
                    "and replace it with an exact column name from the schema."
                ),
            )

        tbl_match = re.search(r'relation "([^"]+)" does not exist', error_msg, re.IGNORECASE)
        if tbl_match:
            sym = tbl_match.group(1)
            return ErrorReflectionHint(
                category=SqlErrorCategory.UNDEFINED_TABLE,
                offending_symbol=sym,
                repair_instruction=(
                    f"Table '{sym}' does not exist. Use the fully qualified schema.table "
                    "names from the pruned catalog."
                ),
            )

        if "must appear in the GROUP BY clause" in error_msg:
            return ErrorReflectionHint(
                category=SqlErrorCategory.GROUPING_ERROR,
                offending_symbol="GROUP BY",
                repair_instruction=(
                    "Every non-aggregated column in SELECT must appear in GROUP BY. "
                    "Add missing columns to GROUP BY or wrap them in an aggregate."
                ),
            )

        if "operator does not exist" in error_msg or "invalid input syntax" in error_msg:
            return ErrorReflectionHint(
                category=SqlErrorCategory.TYPE_MISMATCH,
                offending_symbol="CAST",
                repair_instruction=(
                    "Type mismatch detected. Apply explicit CAST(col AS TYPE) or "
                    "correct the literal format to match the column's data_type."
                ),
            )

        if "statement timeout" in error_msg.lower():
            return ErrorReflectionHint(
                category=SqlErrorCategory.TIMEOUT,
                offending_symbol="TIMEOUT",
                repair_instruction=(
                    "Query exceeded statement_timeout. Tighten the partition-key date range "
                    "or pre-aggregate in a CTE before joining."
                ),
            )

        return ErrorReflectionHint(
            category=SqlErrorCategory.UNKNOWN,
            offending_symbol="",
            repair_instruction=f"Fix SQL error reported by engine: {error_msg[:240]}",
        )


def demo_error_classifier() -> None:
    classifier = SqlErrorClassifier()
    errors = [
        'ERROR: column "s.merchant_cat_id" does not exist',
        'ERROR: column "mc.category_name" must appear in the GROUP BY clause or be used in an aggregate function',
        'ERROR: canceling statement due to statement timeout',
    ]
    for err in errors:
        hint = classifier.classify(err)
        print(f"[{hint.category.value}] symbol={hint.offending_symbol!r} -> {hint.repair_instruction}")


if __name__ == "__main__":
    demo_error_classifier()
