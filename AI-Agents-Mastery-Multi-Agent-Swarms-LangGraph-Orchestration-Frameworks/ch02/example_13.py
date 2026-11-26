def sliding_window_reducer(current_messages: List[str], new_messages: List[str]) -> List[str]:
    """Keeps only the most recent N messages in state to prevent memory bloat."""
    WINDOW_LIMIT = 5
    combined = current_messages + new_messages
    if len(combined) > WINDOW_LIMIT:
        print(f"[REDUCER] Trimming state: Pruning oldest {len(combined) - WINDOW_LIMIT} turns.")
        return combined[-WINDOW_LIMIT:]
    return combined

class TokenManagedState(TypedDict):
    user_query: str
    message_buffer: Annotated[List[str], sliding_window_reducer]
