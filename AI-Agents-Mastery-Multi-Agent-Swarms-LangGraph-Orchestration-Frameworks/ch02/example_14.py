def validate_graph_integrity(graph_app: Any) -> bool:
    """Verifies that all nodes and edges conform to reachability standards."""
    drawable_graph = graph_app.get_graph()
    nodes = set(drawable_graph.nodes.keys())
    edges = drawable_graph.edges
    
    # Assert start and end exist
    assert "__start__" in nodes, "Missing __start__ node in graph."
    assert "__end__" in nodes, "Missing __end__ node in graph."
    
    # Assert every node has at least one incoming and one outgoing path
    for node in nodes:
        if node in ("__start__", "__end__"):
            continue
        incoming = [e for e in edges if e.target == node]
        outgoing = [e for e in edges if e.source == node]
        assert len(incoming) > 0, f"Dead node detected! Node '{node}' has no incoming edges."
        assert len(outgoing) > 0, f"Trap node detected! Node '{node}' has no outgoing edges."
        
    print(f"[CI/CD AUDIT] Graph topology verified! Total Nodes: {len(nodes)}, Total Edges: {len(edges)}.")
    return True
