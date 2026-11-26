import asyncio
from typing import Callable, Any
from dataclasses import dataclass, field

@dataclass
class TaskNode:
    """Represents a single executable node within an Agentic Planning DAG."""
    node_id: str
    func: Callable
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    status: str = "PENDING"  # PENDING | RUNNING | SUCCESS | FAILED

class PlanningDAGExecutor:
    """
    Executes a directed acyclic graph of agent task nodes.
    Automatically extracts parallelism from independent branches.
    """
    def __init__(self, nodes: list[TaskNode]):
        self.nodes = {n.node_id: n for n in nodes}

    async def execute(self) -> dict[str, Any]:
        """Topologically sorts and executes all DAG nodes with maximum parallelism."""
        results = {}
        completed = set()

        while len(completed) < len(self.nodes):
            # Find all nodes whose dependencies are fully satisfied
            ready = [
                node_id for node_id, node in self.nodes.items()
                if node_id not in completed
                and all(dep in completed for dep in node.dependencies)
            ]

            if not ready:
                # Deadlock: no nodes are ready but not all completed
                raise RuntimeError("DAG_EXECUTION_ERROR: Circular dependency or isolated node detected.")

            # Execute all ready nodes concurrently
            tasks = [self._run_node(self.nodes[nid]) for nid in ready]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for node_id, result in zip(ready, batch_results):
                if isinstance(result, Exception):
                    self.nodes[node_id].status = "FAILED"
                    raise RuntimeError(f"Node '{node_id}' failed: {result}")
                self.nodes[node_id].status = "SUCCESS"
                self.nodes[node_id].result = result
                results[node_id] = result
                completed.add(node_id)

        return results

    async def _run_node(self, node: TaskNode) -> Any:
        node.status = "RUNNING"
        return await asyncio.to_thread(node.func)
