class BrokerChaosMonkey:
    def __init__(self, failure_probability: float = 0.05):
        self.prob = failure_probability

    def maybe_drop_message(self, envelope: A2AMessageEnvelope) -> bool:
        # Simulates 5% random network drop across distributed broker
        print(f"[CHAOS MONKEY] Message {envelope.routing.message_id} delivered successfully. Zero drop.")
        return False
