from __future__ import annotations

import ast
from collections import defaultdict, deque


def extract_import_edges(module_name: str, source_code: str) -> list[DependencyEdge]:
    tree = ast.parse(source_code)
    edges: list[DependencyEdge] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                edges.append(
                    DependencyEdge(
                        caller_module=module_name,
                        callee_module=alias.name,
                        imported_symbol="*",
                    )
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                edges.append(
                    DependencyEdge(
                        caller_module=module_name,
                        callee_module=node.module,
                        imported_symbol=alias.name,
                    )
                )
    return edges


def compute_blast_radius(target_module: str, edges: list[DependencyEdge]) -> list[str]:
    reverse_adj: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        reverse_adj[edge.callee_module].add(edge.caller_module)

    visited: set[str] = {target_module}
    queue: deque[str] = deque([target_module])
    impacted: list[str] = []

    while queue:
        curr = queue.popleft()
        for dependent in sorted(reverse_adj[curr]):
            if dependent not in visited:
                visited.add(dependent)
                impacted.append(dependent)
                queue.append(dependent)
    return impacted


if __name__ == "__main__":
    repo_files = {
        "core.db": "async def get_pool(): return None",
        "billing.fees": "from core.db import get_pool\ndef calc(): pass",
        "checkout.api": "from billing.fees import calc\ndef post_order(): pass",
        "jobs.nightly": "import checkout.api\ndef run(): pass",
        "docs.cli": "import json\ndef help_cmd(): pass",
    }
    all_edges: list[DependencyEdge] = []
    for mod, src in repo_files.items():
        all_edges.extend(extract_import_edges(mod, src))

    affected = compute_blast_radius("core.db", all_edges)
    print(f"Total edges={len(all_edges)} Blast radius for 'core.db': {affected}")
