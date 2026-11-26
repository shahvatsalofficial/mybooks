from __future__ import annotations

import hashlib
from typing import List, Tuple
from pydantic import BaseModel


class ParentSection(BaseModel):
    parent_id: str
    section_title: str
    full_text: str


class ChildChunk(BaseModel):
    chunk_id: str
    parent_id: str
    cik: str
    fiscal_year: int
    is_superseded: bool
    text: str


class ParentChildChunker:
    """Builds parent sections and overlapping child chunks for SEC disclosures."""

    @staticmethod
    def chunk_section(
        cik: str,
        fiscal_year: int,
        section_title: str,
        full_text: str,
        child_word_limit: int = 40,
        overlap_words: int = 10,
    ) -> Tuple[ParentSection, List[ChildChunk]]:
        parent_id = f"par_{hashlib.sha256(f'{cik}:{fiscal_year}:{section_title}'.encode()).hexdigest()[:12]}"
        parent = ParentSection(
            parent_id=parent_id,
            section_title=section_title,
            full_text=full_text.strip(),
        )
        words = full_text.split()
        children: List[ChildChunk] = []
        step = max(1, child_word_limit - overlap_words)

        for idx in range(0, len(words), step):
            slice_words = words[idx : idx + child_word_limit]
            if not slice_words:
                break
            chunk_text = " ".join(slice_words)
            cid = f"{parent_id}_c{len(children):03d}"
            children.append(
                ChildChunk(
                    chunk_id=cid,
                    parent_id=parent_id,
                    cik=cik,
                    fiscal_year=fiscal_year,
                    is_superseded=False,
                    text=chunk_text,
                )
            )
            if idx + child_word_limit >= len(words):
                break
        return parent, children


if __name__ == "__main__":
    sample_note = (
        "Note 9 Long-Term Debt. On March 14, 2025, the Company issued $1.5 billion of "
        "Senior Unsecured Notes due 2032 bearing fixed interest at 5.125% payable semi-annually. "
        "The credit facility includes a maximum consolidated net leverage covenant of 3.50x EBITDA."
    )
    parent, kids = ParentChildChunker.chunk_section(
        "0000950170", 2025, "Note 9: Long-Term Debt", sample_note, child_word_limit=22, overlap_words=5
    )
    print(f"Parent ID: {parent.parent_id} | Child chunks: {len(kids)}")
    for c in kids:
        print(f"  {c.chunk_id}: {c.text}")
