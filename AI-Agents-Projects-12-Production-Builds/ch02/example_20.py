from collections import defaultdict, deque

def topological_refactor_order(modules: list[str], edges: list[DependencyEdge]) -> list[str]:
    mod_set = set(modules)
    in_deg = {m: 0 for m in mod_set}
    callers: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e.caller_module in mod_set and e.callee_module in mod_set:
            callers[e.callee_module].append(e.caller_module)
            in_deg[e.caller_module] += 1
    q = deque(sorted(m for m, d in in_deg.items() if d == 0))
    order: list[str] = []
    while q:
        curr = q.popleft()
        order.append(curr)
        for nxt in sorted(callers[curr]):
            in_deg[nxt] -= 1
            if in_deg[nxt] == 0:
                q.append(nxt)
    return order
