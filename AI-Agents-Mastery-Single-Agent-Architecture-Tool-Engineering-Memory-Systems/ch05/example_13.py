import asyncio
import time
from typing import Dict, List, Set, Any

class SpeculativeDAGExecutor:
    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = {}
        self.results: Dict[str, Any] = {}

    def add_tool_task(self, task_id: str, depends_on: List[str] = None) -> None:
        self.dependencies[task_id] = set(depends_on or [])

    async def _run_task(self, task_id: str) -> None:
        # Wait for all prerequisite tasks to complete
        while not self.dependencies[task_id].issubset(self.results.keys()):
            await asyncio.sleep(0.005)

        start = time.perf_counter()
        await asyncio.sleep(0.02)  # Simulated I/O
        self.results[task_id] = f"Result of {task_id} (Completed in 20ms)"
        print(f"[DAG EXECUTOR] Completed '{task_id}'")

    async def execute_dag(self) -> Dict[str, Any]:
        tasks = [asyncio.create_task(self._run_task(tid)) for tid in self.dependencies]
        await asyncio.gather(*tasks)
        return self.results

async def main():
    dag = SpeculativeDAGExecutor()
    # Task A & B run concurrently; Task C requires both A & B
    dag.add_tool_task("Fetch_Customer_Profile", depends_on=[])
    dag.add_tool_task("Fetch_Credit_Score", depends_on=[])
    dag.add_tool_task("Evaluate_Loan_Eligibility", depends_on=["Fetch_Customer_Profile", "Fetch_Credit_Score"])

    start = time.perf_counter()
    res = await dag.execute_dag()
    print(f"DAG Execution finished in {(time.perf_counter() - start)*1000:.1f}ms")

asyncio.run(main())
