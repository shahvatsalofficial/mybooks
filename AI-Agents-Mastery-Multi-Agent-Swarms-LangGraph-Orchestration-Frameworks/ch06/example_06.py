def publish_a2a_to_queue(envelope: A2AMessageEnvelope, routing_key: str, amqp_url: str = "amqp://localhost:5672/"):
    connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
    channel = connection.channel()
    
    # Serialize envelope to JSON
    body_bytes = envelope.model_dump_json().encode("utf-8")
    
    # Publish with delivery_mode=2 (Persistent on disk)
    channel.basic_publish(
        exchange="agent.events.direct",
        routing_key=routing_key,
        body=body_bytes,
        properties=pika.BasicProperties(
            delivery_mode=2, # Persistent message
            content_type="application/json",
            correlation_id=envelope.routing.conversation_id,
            message_id=envelope.routing.message_id,
            headers={"root_trace_id": envelope.routing.root_trace_id}
        )
    )
    print(f"[AMQP PUBLISH] Published persistent envelope {envelope.routing.message_id} to '{routing_key}'.")
    connection.close()
