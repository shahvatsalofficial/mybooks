await client.beta.threads.runs.submit_tool_outputs(
    thread_id=thread_id,
    run_id=run.id,
    tool_outputs=[
        {
            "tool_call_id": "call_ledger_884",
            "output": json.dumps({"balance": 142500.00, "status": "ACTIVE"})
        }
    ]
)
