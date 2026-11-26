def should_continue_router(state: ResearchGraphState) -> Literal["researcher_node", "__end__"]:
    """Dynamic router deciding whether to cycle back or terminate."""
    if state["is_approved"]:
        print("[ROUTER] Approved! Routing to graph terminal (__end__).")
        return "__end__"
    
    if state["revision_count"] >= 3:
        print("[ROUTER] WARNING: Maximum revision ceiling (3) reached. Forcing termination.")
        return "__end__"
        
    print("[ROUTER] Iteration rejected. Cycling back to researcher_node...")
    return "researcher_node"
