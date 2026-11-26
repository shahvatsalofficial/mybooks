class RedisStreamsDispatcher:
    def __init__(self, stream_name: str = "agent_stream_events"):
        self.stream_name = stream_name

    def emit_event(self, event_name: str, envelope: A2AMessageEnvelope):
        payload_json = envelope.model_dump_json()
        print(f"[REDIS STREAM] Emitting event '{event_name}' to stream '{self.stream_name}'...")
        # redis_client.xadd(self.stream_name, {"event": event_name, "envelope": payload_json})
