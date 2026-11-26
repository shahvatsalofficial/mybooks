import asyncio
from typing import List, Dict, Any
from anthropic import AsyncAnthropic

class MapReduceDocumentPipeline:
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def _map_document(self, doc_id: str, doc_content: str) -> Dict[str, str]:
        """Map worker: extracts key operational findings from a single document."""
        prompt = f"Document ID: {doc_id}\n\nContent:\n{doc_content}\n\nExtract key findings, risk items, and quantitative metrics."
        res = await self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=800,
            temperature=0.0,
            system="You are a Document Extraction Specialist. Be terse and quantitative.",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"doc_id": doc_id, "summary": res.content[0].text.strip()}

    async def _reduce_summaries(self, map_results: List[Dict[str, str]]) -> str:
        """Reduce stage: aggregates and reconciles findings across all documents."""
        combined_text = "\n\n".join([
            f"--- Document {item['doc_id']} ---\n{item['summary']}"
            for item in map_results
        ])
        prompt = f"Extracted Findings Across Corpus:\n{combined_text}\n\nSynthesize a unified executive briefing identifying cross-cutting trends and contradictory statements."
        res = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.0,
            system="You are an Executive Intelligence Synthesizer. Highlight cross-document consensus and divergences.",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.content[0].text.strip()

    async def execute_map_reduce(self, documents: Dict[str, str]) -> str:
        # Concurrent Map Phase
        map_tasks = [
            self._map_document(doc_id, content)
            for doc_id, content in documents.items()
        ]
        map_results = await asyncio.gather(*map_tasks)

        # Sequential Reduce Phase
        final_briefing = await self._reduce_summaries(map_results)
        return final_briefing
