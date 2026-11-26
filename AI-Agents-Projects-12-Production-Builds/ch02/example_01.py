from __future__ import annotations

import hashlib
from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SymbolKind(str, Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    METHOD = "method"


class SymbolSpan(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol_id: str = Field(min_length=3, max_length=200)
    file_path: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: SymbolKind
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    source_sha256: str = Field(min_length=16)

    @model_validator(mode="after")
    def validate_line_order(self) -> SymbolSpan:
        if self.end_line < self.start_line:
            raise ValueError(f"end_line ({self.end_line}) < start_line ({self.start_line})")
        return self


class DependencyEdge(BaseModel):
    model_config = ConfigDict(frozen=True)

    caller_module: str
    callee_module: str
    imported_symbol: str


class SearchReplaceEdit(BaseModel):
    model_config = ConfigDict(frozen=True)

    edit_id: str = Field(min_length=2, max_length=64)
    file_path: str = Field(min_length=1)
    target_symbol: str = Field(min_length=1)
    search_block: str = Field(min_length=5)
    replace_block: str = Field(min_length=1)
    rationale: str = Field(min_length=10, max_length=400)

    @model_validator(mode="after")
    def ensure_mutation(self) -> SearchReplaceEdit:
        if self.search_block == self.replace_block:
            raise ValueError("search_block and replace_block must differ")
        return self


class SandboxVerdict(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    exit_code: int
    tests_passed: int = Field(ge=0)
    tests_failed: int = Field(ge=0)
    coverage_pct: Annotated[float, Field(ge=0.0, le=100.0)]
    duration_ms: float = Field(ge=0.0)
    failure_excerpt: str = ""

    @property
    def is_green(self) -> bool:
        return self.exit_code == 0 and self.tests_failed == 0


if __name__ == "__main__":
    sample_code = "def compute_fee(amount: int) -> float:\n    return round(amount * 0.025, 2)\n"
    span = SymbolSpan(
        symbol_id="billing.fees:compute_fee",
        file_path="billing/fees.py",
        name="compute_fee",
        kind=SymbolKind.FUNCTION,
        start_line=1,
        end_line=2,
        source_sha256=hashlib.sha256(sample_code.encode("utf-8")).hexdigest(),
    )
    edit = SearchReplaceEdit(
        edit_id="ed_01",
        file_path="billing/fees.py",
        target_symbol="compute_fee",
        search_block="def compute_fee(amount: int) -> float:\n    return round(amount * 0.025, 2)",
        replace_block="def compute_fee(amount: int, rate: float = 0.025) -> float:\n    return round(amount * rate, 2)",
        rationale="Parameterize fee rate with backward-compatible default.",
    )
    verdict = SandboxVerdict(
        run_id="sbx_9921",
        exit_code=0,
        tests_passed=14,
        tests_failed=0,
        coverage_pct=94.5,
        duration_ms=412.8,
    )
    print(f"Span={span.symbol_id} lines={span.start_line}-{span.end_line}")
    print(f"Edit={edit.edit_id} target={edit.target_symbol} green={verdict.is_green}")
