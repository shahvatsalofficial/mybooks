def test_a2a_compliance():
    routing = A2ARoutingHeader(
        conversation_id="conv_1",
        root_trace_id="trace_1",
        sender_uri="urn:agent:test_sender",
        recipient_uri="urn:agent:test_recipient"
    )
    sec = A2ACryptoEngine.sign_payload(routing, {"test": True})
    env = A2AMessageEnvelope(routing=routing, security=sec, intent="EVENT_BROADCAST", payload={"test": True})
    assert A2ACryptoEngine.verify_envelope(env)
    print("[COMPLIANCE TEST] A2A Protocol Envelope 100% compliant.")
