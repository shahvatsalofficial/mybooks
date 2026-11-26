# Fetch the 20 most recent messages (Reverse Chronological Order)
messages_page = await client.beta.threads.messages.list(
    thread_id=thread.id,
    limit=20,
    order="desc"
)

# Fetch older historical messages before a specific cursor
if messages_page.has_more:
    oldest_message_id = messages_page.data[-1].id
    historical_page = await client.beta.threads.messages.list(
        thread_id=thread.id,
        limit=20,
        order="desc",
        before=oldest_message_id
    )
