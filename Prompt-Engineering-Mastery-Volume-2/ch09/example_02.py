import asyncio
from typing import List, Dict, Any
from anthropic import AsyncAnthropic

class HierarchicalDocumentCompressor:
    def __init__(self, api_key: str, chunk_size_chars: int = 6000):
        self.client = AsyncAnthropic(api_key=api_key)
        self.chunk_size = chunk_size_chars

    def _chunk_text(self, text: str) -> List[str]:
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size])
        return chunks

    async def _summarize_leaf(self, chunk_id: int, chunk_text: str) -> str:
        prompt = (
            f"Chunk {chunk_id} Content:\n{chunk_text}\n\n"
            "Compress this document section into a dense factual summary. "
            "Extract: 1) Quantitative metrics, 2) Named entities, 3) Core policy decisions. "
            "Eliminate conversational prose and formatting filler."
        )
        res = await self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=400,
            temperature=0.0,
            system="You are an Information Entropy Maximizer.",
            messages=[{"role": "user", "content": prompt}]
        )
        return f"[Section {chunk_id}]: " + res.content[0].text.strip()

    async def _synthesize_root(self, leaf_summaries: List[str]) -> str:
        combined = "\n\n".join(leaf_summaries)
        prompt = (
            f"Section Summaries:\n{combined}\n\n"
            "Synthesize an Executive Briefing representing the entire document. "
            "Preserve cross-section dependencies and all critical quantitative thresholds."
        )
        res = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.0,
            system="You are an Executive Intelligence Synthesizer.",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.content[0].text.strip()

    async def compress_corpus(self, full_text: str) -> Dict[str, Any]:
        chunks = self._chunk_text(full_text)
        print(f"📦 Partitioned document into {len(chunks)} leaf chunks. Executing Tier-1 Map...")

        # Tier-1 Concurrent Leaf Summarization
        leaf_tasks = [self._summarize_leaf(idx, c) for idx, c in enumerate(chunks)]
        leaf_summaries = await asyncio.gather(*leaf_tasks)

        # Tier-2 Root Synthesis
        print("🌲 Tier-1 complete. Executing Tier-2 Root Synthesis...")
        root_summary = await self._synthesize_root(leaf_summaries)

        return {
            "original_char_count": len(full_text),
            "leaf_summaries_count": len(leaf_summaries),
            "root_summary": root_summary,
            "compression_ratio": round(len(full_text) / (len(root_summary) + 1), 2)
        }
