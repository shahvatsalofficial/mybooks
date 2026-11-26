class A2APathwayRouter:
    def __init__(self):
        self.routes: Dict[str, Any] = {} # Map recipient_uri to agent dispatch callable
        self.message_ledger: List[A2AMessageEnvelope] = []

    def register_agent_endpoint(self, agent_uri: str, handler_callable: Any):
        print(f"[A2A ROUTER] Registering endpoint: '{agent_uri}'")
        self.routes[agent_uri] = handler_callable

    def route_envelope(self, envelope: A2AMessageEnvelope) -> Optional[A2AMessageEnvelope]:
        # 1. Enforce Cryptographic Verification
        A2ACryptoEngine.verify_envelope(envelope)
        
        # 2. Check Hop Count Circuit Breaker
        if envelope.routing.hop_count > 8:
            raise RecursionError(f"Hop count exceeded (hop_count={envelope.routing.hop_count}). Potential routing loop!")

        # 3. Dispatch to target agent endpoint
        target = envelope.routing.recipient_uri
        handler = self.routes.get(target)
        if not handler:
            raise KeyError(f"Destination agent URI '{target}' not registered in router.")
            
        print(f"[A2A ROUTER] Routing message {envelope.routing.message_id} from '{envelope.routing.sender_uri}' to '{target}'...")
        self.message_ledger.append(envelope)
        
        # Invoke handler with incremented hop count
        return handler(envelope)
