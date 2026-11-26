def task_completion_telemetry_callback(output: Any):
    """Callback triggered automatically upon completion of any crew task."""
    print(f"\n[TELEMETRY CALLBACK] Task Completed!")
    print(f"Exported Raw Length: {len(str(output.raw))} characters")
    print(f"Token Consumption: {output.token_usage}")

research_task.callback = task_completion_telemetry_callback
