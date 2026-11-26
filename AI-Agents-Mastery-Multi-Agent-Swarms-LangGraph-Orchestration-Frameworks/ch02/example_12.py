def aggregate_sections_node(state: SectionProcessingState) -> Dict[str, Any]:
    """Gathers all dynamic summaries once worker tasks complete."""
    summaries = state["processed_summaries"]
    print(f"[AGGREGATOR] Gathered {len(summaries)} completed section summaries.")
    combined_report = "\n".join(summaries)
    return {"processed_summaries": [f"=== FINAL AUDIT REPORT ===\n{combined_report}"]}
