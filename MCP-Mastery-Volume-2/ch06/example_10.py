def sanitize_for_openai(schema: dict) -> dict:
    """Transforms advanced JSON Schema constructs into OpenAI-compatible equivalents."""
    cleaned = dict(schema)
    
    # 1. Convert prefixItems to standard items
    if "prefixItems" in cleaned:
        cleaned["items"] = cleaned.pop("prefixItems")[0]
        
    # 2. Prune unsupported conditional keywords
    for keyword in ["if", "then", "else", "dependentRequired", "unevaluatedProperties"]:
        cleaned.pop(keyword, None)
        
    # 3. Recursively sanitize nested object properties
    if cleaned.get("type") == "object" and "properties" in cleaned:
        for prop_name, prop_spec in cleaned["properties"].items():
            cleaned["properties"][prop_name] = sanitize_for_openai(prop_spec)
            
    return cleaned
