run = await client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    max_prompt_tokens=8000,        # Hard ceiling on ingested context tokens
    max_completion_tokens=1500,    # Hard ceiling on output tokens
    truncation_strategy={
        "type": "last_messages",
        "last_messages": 10        # Ingest strictly the most recent 10 messages
    }
)
