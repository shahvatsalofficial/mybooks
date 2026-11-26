def assert_no_duplicate_consecutive_calls(calls: List[RecordedToolCall]):
    for i in range(len(calls) - 1):
        c1, c2 = calls[i], calls[i+1]
        if c1.tool_name == c2.tool_name and c1.arguments == c2.arguments:
            raise AssertionError(f"Degraded Loop: Consecutive duplicate tool calls detected for '{c1.tool_name}' at steps {c1.step_number} and {c2.step_number}.")
