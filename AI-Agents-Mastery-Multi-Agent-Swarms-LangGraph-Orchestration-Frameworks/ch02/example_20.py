def versioned_diff_reducer(current_dict: Dict[str, Any], new_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Merges two dictionaries respecting internal version timestamps."""
    merged = current_dict.copy()
    for k, v in new_dict.items():
        if isinstance(v, dict) and "v" in v:
            curr_v = merged.get(k, {}).get("v", 0)
            if v["v"] >= curr_v:
                merged[k] = v
        else:
            merged[k] = v
    return merged

class VersionedStateGraphSchema(TypedDict):
    shared_data: Annotated[Dict[str, Any], versioned_diff_reducer]
