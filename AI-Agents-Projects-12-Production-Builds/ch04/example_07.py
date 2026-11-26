from __future__ import annotations

import re
from typing import List
from pydantic import BaseModel


class CrossReferenceLink(BaseModel):
    source_chunk_id: str
    referenced_notes: List[str]


class FootnoteCrossReferencer:
    """Detects explicit SEC footnote references inside MD&A text."""

    NOTE_RE = re.compile(r"\bNote\s+(\d{1,2})\b", re.IGNORECASE)

    @classmethod
    def extract_links(cls, chunk_id: str, text: str) -> CrossReferenceLink:
        nums = sorted({f"Note {m.group(1)}" for m in cls.NOTE_RE.finditer(text)})
        return CrossReferenceLink(source_chunk_id=chunk_id, referenced_notes=nums)


if __name__ == "__main__":
    mda = "Interest expense rose 18% YoY following the senior notes issuance (see Note 9 and Note 14)."
    print(FootnoteCrossReferencer.extract_links("mda_c012", mda).model_dump_json())
