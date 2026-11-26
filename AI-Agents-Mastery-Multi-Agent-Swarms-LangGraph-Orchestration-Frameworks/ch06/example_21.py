def publish_prioritized_a2a_message(channel: Any, envelope: A2AMessageEnvelope, priority_level: int = 0):
    body = envelope.model_dump_json().encode("utf-8")
    channel.basic_publish(
        exchange="agent.events.direct",
        routing_key="security_triage_queue",
        body=body,
        properties=pika.BasicProperties(
            priority=priority_level, # 0 to 10 scale
            delivery_mode=2
        )
    )
    print(f"[AMQP PRIORITY] Dispatched Envelope {envelope.routing.message_id} with Priority Level {priority_level}.")
