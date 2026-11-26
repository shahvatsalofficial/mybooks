# DANGEROUS CODE PATTERN THAT TRIGGERED THE COLLAPSE:
for attempt in range(5):
    try:
        return openai_client.chat.completions.create(...)
    except RateLimitError:
        time.sleep(1.0) # Flat 1-second retry with zero jitter!
