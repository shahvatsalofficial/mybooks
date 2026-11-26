class AMQPTransactionCompensator:
    @staticmethod
    def broadcast_compensation_event(channel: Any, tx_id: str, reason: str):
        payload = json.dumps({"transaction_id": tx_id, "action": "ROLLBACK_ALL", "reason": reason})
        channel.basic_publish(
            exchange="agent.compensation.fanout",
            routing_key="",
            body=payload.encode("utf-8")
        )
        print(f"[AMQP COMPENSATION] Broadcasted rollback for TX {tx_id}: {reason}")
