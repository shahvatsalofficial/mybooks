def enforce_disambiguation_guard(results: List[Any], max_allowed: int = 1) -> str:
    if len(results) > max_allowed:
        return f"STOP GATE: Query returned {len(results)} matches. Disambiguation required from human operator. Do not retry."
    return json.dumps(results)
