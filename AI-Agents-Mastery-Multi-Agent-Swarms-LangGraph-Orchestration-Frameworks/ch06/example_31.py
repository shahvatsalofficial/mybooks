# Hardened Consumer Rejection Pattern:
def safe_message_handler(channel, delivery_tag, body):
    try:
        # Validate schema before processing
        envelope = A2AMessageEnvelope.model_validate_json(body)
        process_task(envelope)
        channel.basic_ack(delivery_tag=delivery_tag)
    except Exception as exc:
        print(f"[REJECTION] Poison pill discarded to DLQ: {exc}")
        # Never requeue deterministically failing messages!
        channel.basic_nack(delivery_tag=delivery_tag, requeue=False)
