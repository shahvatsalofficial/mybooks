def setup_alternate_exchange_topology(channel: Any):
    # 1. Declare unroutable fallback exchange
    channel.exchange_declare(exchange="unroutable.events.fanout", exchange_type="fanout", durable=True)
    channel.queue_declare(queue="unroutable_audit_sink", durable=True)
    channel.queue_bind(exchange="unroutable.events.fanout", queue="unroutable_audit_sink")

    # 2. Declare primary exchange with alternate-exchange argument
    channel.exchange_declare(
        exchange="agent.events.direct",
        exchange_type="direct",
        durable=True,
        arguments={"alternate-exchange": "unroutable.events.fanout"}
    )
    print("[AMQP] Alternate exchange configured: Zero message loss on missing routing keys.")
