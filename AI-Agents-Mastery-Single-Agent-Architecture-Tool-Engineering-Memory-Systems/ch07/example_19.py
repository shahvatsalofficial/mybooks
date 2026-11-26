def assert_step_budget(trajectory: List[Any], baseline_steps: int, max_allowed_creep: float = 0.20):
    actual_steps = len(trajectory)
    ceiling = int(baseline_steps * (1.0 + max_allowed_creep))
    if actual_steps > ceiling:
        raise AssertionError(f"Step Creep Detected: Trajectory took {actual_steps} steps (Ceiling: {ceiling}).")
