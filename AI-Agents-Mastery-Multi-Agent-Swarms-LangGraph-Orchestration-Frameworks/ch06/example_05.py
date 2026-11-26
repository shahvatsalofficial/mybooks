import pika

class RabbitMQAgentTopology:
    def __init__(self, amqp_url: str = "amqp://guest:guest@localhost:5672/"):
        self.amqp_url = amqp_url
        self.exchange_name = "agent.events.direct"

    def declare_topology(self, agent_queue_name: str, routing_key: str):
        """Provisions durable exchanges, queues, and routing keys."""
        connection = pika.BlockingConnection(pika.URLParameters(self.amqp_url))
        channel = connection.channel()

        # 1. Declare durable direct exchange
        channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type="direct",
            durable=True
        )

        # 2. Declare durable worker queue with Dead-Letter-Exchange binding
        channel.queue_declare(
            queue=agent_queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "agent.dead_letter.exchange",
                "x-dead-letter-routing-key": "dead_letter_sink"
            }
        )

        # 3. Bind queue to exchange
        channel.queue_bind(
            exchange=self.exchange_name,
            queue=agent_queue_name,
            routing_key=routing_key
        )
        print(f"[AMQP] Declared topology: Queue '{agent_queue_name}' bound to '{routing_key}'.")
        connection.close()
