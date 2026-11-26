def estimate_tokens(text: str) -> int:
    return int(len(text) / 3.2)

def token_budget_guard(messages: list[PromptMessage], max_tokens: int = 50000) -> list[PromptMessage]:
    total_tokens = 0
    guarded_messages = []

    for msg in messages:
        if isinstance(msg.content, TextContent):
            tokens = estimate_tokens(msg.content.text)
            total_tokens += tokens
            guarded_messages.append(msg)
        elif isinstance(msg.content, EmbeddedResource):
            res_text = getattr(msg.content.resource, "text", "")
            tokens = estimate_tokens(res_text)
            if total_tokens + tokens > max_tokens:
                # Truncate resource to fit budget
                allowed_chars = int((max_tokens - total_tokens) * 3.2)
                truncated_text = res_text[:allowed_chars] + "\n...[TRUNCATED: Budget Cap Exceeded]"
                msg.content.resource.text = truncated_text
                total_tokens = max_tokens
            else:
                total_tokens += tokens
            guarded_messages.append(msg)

    return guarded_messages
