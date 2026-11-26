import concurrent.futures
from typing import List

class MapReduceSwarm:
    def __init__(self, max_concurrency: int = 4):
        self.max_concurrency = max_concurrency
        self.worker = ResearchWorker(name="ParallelResearcher")

    def _execute_subtask(self, query_chunk: str) -> str:
        msg = AgentMessage(
            sender="MapReduceCoordinator",
            sender_role=AgentRole.SUPERVISOR,
            recipient=self.worker.name,
            message_type=MessageType.TASK_ASSIGNMENT,
            content=query_chunk
        )
        res = self.worker.process_message(msg)
        return res.content

    def map_reduce(self, queries: List[str]) -> str:
        print(f"[MAP-REDUCE] Dispatching {len(queries)} tasks across pool (max_concurrency={self.max_concurrency})...")
        t0 = time.time()
        
        # 1. Map Phase (Parallel Fan-Out)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrency) as executor:
            future_to_query = {executor.submit(self._execute_subtask, q): q for q in queries}
            mapped_results = []
            for future in concurrent.futures.as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    data = future.result()
                    mapped_results.append(data)
                except Exception as exc:
                    mapped_results.append(f"ERROR on query '{query}': {exc}")

        # 2. Reduce Phase (Synthesis)
        elapsed = (time.time() - t0) * 1000
        print(f"[MAP-REDUCE] Fan-out completed in {elapsed:.2f}ms. Synthesizing {len(mapped_results)} partitions...")
        combined_digest = "\n---\n".join(mapped_results)
        return f"=== CONSOLIDATED SWARM REDUCE SUMMARY ===\n{combined_digest}"
