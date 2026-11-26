from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from typing import Protocol


class PlannerLLM(Protocol):
    async def generate_dag(self, objective: str) -> ResearchDAG: ...


class HeuristicFallbackPlanner:
    """Deterministic multi-aspect decomposer used when LLM structured output fails."""

    async def generate_dag(self, objective: str) -> ResearchDAG:
        await asyncio.sleep(0.01)
        clean = objective.strip().rstrip("?")
        nodes = [
            SubQueryNode(
                node_id="q_primary_spec",
                query_text=f"{clean} official specification documentation benchmarks",
                target_tiers=[SourceTier.PRIMARY_OFFICIAL],
                wave_index=0,
            ),
            SubQueryNode(
                node_id="q_empirical_eval",
                query_text=f"{clean} production latency throughput evaluation",
                target_tiers=[SourceTier.PEER_REVIEWED, SourceTier.ENGINEERING_BLOG],
                wave_index=0,
            ),
            SubQueryNode(
                node_id="q_risk_postmortem",
                query_text=f"{clean} limitations failure modes security audit",
                target_tiers=[SourceTier.PRIMARY_OFFICIAL, SourceTier.ENGINEERING_BLOG],
                depends_on=["q_primary_spec"],
                wave_index=1,
            ),
        ]
        return ResearchDAG(root_objective=objective, nodes=nodes)


def build_execution_waves(dag: ResearchDAG) -> list[list[SubQueryNode]]:
    node_map = {n.node_id: n for n in dag.nodes}
    in_degree = {n.node_id: len(n.depends_on) for n in dag.nodes}
    dependents: dict[str, list[str]] = defaultdict(list)
    for n in dag.nodes:
        for dep in n.depends_on:
            dependents[dep].append(n.node_id)

    queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
    waves: list[list[SubQueryNode]] = []

    while queue:
        wave_size = len(queue)
        current_wave: list[SubQueryNode] = []
        for _ in range(wave_size):
            nid = queue.popleft()
            current_wave.append(node_map[nid])
            for child in dependents[nid]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        waves.append(current_wave)
    return waves


async def main() -> None:
    planner = HeuristicFallbackPlanner()
    dag = await planner.generate_dag("Compare PyTorch 2.6 torch.compile vs TensorRT-LLM for Llama-3 70B")
    waves = build_execution_waves(dag)
    for idx, wave in enumerate(waves):
        ids = ", ".join(n.node_id for n in wave)
        print(f"Wave {idx}: [{ids}] ({len(wave)} parallel tasks)")


if __name__ == "__main__":
    asyncio.run(main())
