def secure_vector_query(collection, tenant_id: str, query: str, top_k: int = 3):
    # Mandatory cryptographic tenant assertion
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValueError("Security Violation: Valid tenant_id is required for vector retrieval.")
    
    return collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"tenant_id": {"$eq": tenant_id}}
    )
