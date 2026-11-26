def merge_subgraph_resolutions(current: List[str], updates: List[str]) -> List[str]:
    """Idempotent set-union reducer for concurrent branch resolutions."""
    merged = list(dict.fromkeys(current + updates)) # Preserves order without duplicates
    return merged

class ConcurrentSwarmState(TypedDict):
    ticket_id: str
    resolutions: Annotated[List[str], merge_subgraph_resolutions]
