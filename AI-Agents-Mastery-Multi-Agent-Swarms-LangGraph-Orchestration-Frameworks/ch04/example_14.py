def enforce_security_preflight(agent: Agent, task: Task) -> bool:
    """Pre-flight check executed before agent starts processing a task."""
    assert agent.role != "", "Agent must possess non-empty role."
    assert len(task.expected_output) > 10, "Task must specify clear expected output."
    print(f"[PREFLIGHT] Agent '{agent.role}' validated for task '{task.description[:30]}...'")
    return True
