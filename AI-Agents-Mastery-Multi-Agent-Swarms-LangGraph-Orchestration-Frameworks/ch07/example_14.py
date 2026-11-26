def validate_state_integrity(raw_json: str) -> VersionedState:
    try:
        return VersionedState.model_validate_json(raw_json)
    except Exception as exc:
        raise ValueError(f"State payload corrupted: {exc}")
