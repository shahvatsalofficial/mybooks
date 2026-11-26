class AsyncDocumentBatchProcessor:
    def __init__(self, max_concurrency: int = 4):
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def _process_single(self, doc_id: str, text: str) -> Dict[str, Any]:
        async with self.semaphore:
            # Emulating LLM entity extraction call
            await asyncio.sleep(0.02)
            word_count = len(text.split())
            return {"doc_id": doc_id, "status": "processed", "entities_found": max(1, word_count // 10)}

    async def process_batch(self, docs: Dict[str, str]) -> List[Dict[str, Any]]:
        tasks = [self._process_single(doc_id, text) for doc_id, text in docs.items()]
        return await asyncio.gather(*tasks)

# Verification
async def run_batch_demo():
    processor = AsyncDocumentBatchProcessor(max_concurrency=3)
    documents = {f"DOC_{i}": f"Document content payload with {i*10} words of data." for i in range(1, 7)}
    res = await processor.process_batch(documents)
    print("Batch Processed Count:", len(res))

asyncio.run(run_batch_demo())
