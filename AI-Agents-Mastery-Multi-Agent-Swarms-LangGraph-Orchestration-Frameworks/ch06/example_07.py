def start_agent_amqp_consumer(queue_name: str, amqp_url: str = "amqp://localhost:5672/"):
    connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
    channel = connection.channel()
    
    # Fair dispatch: prefetch_count=1 ensures worker only takes 1 task at a time
    channel.basic_qos(prefetch_count=1)

    def on_message_received(ch, method, properties, body):
        try:
            raw_json = json.loads(body.decode("utf-8"))
            envelope = A2AMessageEnvelope(**raw_json)
            
            # Verify cryptographic signature
            A2ACryptoEngine.verify_envelope(envelope)
            print(f"[CONSUMER] Processing verified task: {envelope.routing.message_id}")
            
            # Manual ACK on successful completion
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            print(f"[CONSUMER ERROR] Task failed: {exc}. Rejecting to DLQ...")
            # NACK and do not requeue -> automatically routes to Dead-Letter Queue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=queue_name, on_message_callback=on_message_received)
    print(f"[AMQP] Worker listening on '{queue_name}'...")
