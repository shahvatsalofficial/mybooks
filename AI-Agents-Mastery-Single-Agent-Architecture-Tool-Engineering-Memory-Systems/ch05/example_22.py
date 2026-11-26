def validate_agent_execution_trajectory(intermediate_steps: List[Tuple[Any, str]]) -> bool:
    for action, observation in intermediate_steps:
        # Halt execution if any critical tool returned an unhandled error
        if "error" in observation.lower() or "timed out" in observation.lower():
            raise RuntimeError(f"Underwriting Safety Intercept: Critical tool '{action.tool}' failed: {observation}")
    return True
