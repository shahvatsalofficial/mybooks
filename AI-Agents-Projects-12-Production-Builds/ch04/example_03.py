from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel


class IndexedFilingRecord(BaseModel):
    cik: str
    form_type: str
    report_date: str
    accession_number: str
    is_superseded: bool = False


class FilingDeltaDetector:
    """Detects restated or amended SEC filings and invalidates stale index entries."""

    def __init__(self) -> None:
        self._registry: Dict[str, IndexedFilingRecord] = {}

    def register_or_supersede(self, incoming: IndexedFilingRecord) -> List[str]:
        key = f"{incoming.cik}:{incoming.report_date}:{incoming.form_type.replace('/A', '')}"
        actions: List[str] = []
        existing = self._registry.get(key)

        if existing is None:
            self._registry[key] = incoming
            actions.append(f"INDEX_NEW:{incoming.accession_number}")
            return actions

        if existing.accession_number != incoming.accession_number:
            existing.is_superseded = True
            self._registry[key] = incoming
            actions.append(f"SUPERSEDE:{existing.accession_number}")
            actions.append(f"INDEX_AMENDMENT:{incoming.accession_number}")
        else:
            actions.append(f"SKIP_UNCHANGED:{incoming.accession_number}")
        return actions


if __name__ == "__main__":
    detector = FilingDeltaDetector()
    orig = IndexedFilingRecord(
        cik="0000950170",
        form_type="10-K",
        report_date="2025-12-31",
        accession_number="0000950170-26-014210",
    )
    amend = IndexedFilingRecord(
        cik="0000950170",
        form_type="10-K/A",
        report_date="2025-12-31",
        accession_number="0000950170-26-019884",
    )
    print("Initial:", detector.register_or_supersede(orig))
    print("Restatement:", detector.register_or_supersede(amend))
