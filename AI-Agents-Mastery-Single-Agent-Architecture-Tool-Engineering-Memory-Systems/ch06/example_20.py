def verify_document_freshness(doc_metadata: Dict[str, Any], max_age_days: int = 30) -> bool:
    doc_timestamp = doc_metadata.get("updated_at", 0)
    current_time = time.time()
    if (current_time - doc_timestamp) > (max_age_days * 86400):
        raise ValueError("Index Freshness Violation: Retrieved document exceeds 30-day freshness SLA.")
    return True
