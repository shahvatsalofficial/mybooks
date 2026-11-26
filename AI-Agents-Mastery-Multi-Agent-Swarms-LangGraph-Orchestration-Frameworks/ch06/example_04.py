def mock_security_analyst_agent(envelope: A2AMessageEnvelope) -> A2AMessageEnvelope:
    print(f"  [AGENT: SecurityAnalyst] Received payload: {envelope.payload}")
    finding = {"status": "CLEAN", "vulnerabilities": 0}
    
    # Formulate response envelope
    resp_routing = A2ARoutingHeader(
        conversation_id=envelope.routing.conversation_id,
        root_trace_id=envelope.routing.root_trace_id,
        parent_id=envelope.routing.message_id,
        hop_count=envelope.routing.hop_count + 1,
        sender_uri="urn:agent:security_analyst_01",
        recipient_uri=envelope.routing.sender_uri
    )
    resp_sec = A2ACryptoEngine.sign_payload(resp_routing, finding)
    
    return A2AMessageEnvelope(
        routing=resp_routing,
        security=resp_sec,
        intent="TASK_RESPONSE",
        payload=finding
    )

if __name__ == "__main__":
    router = A2APathwayRouter()
    router.register_agent_endpoint("urn:agent:security_analyst_01", mock_security_analyst_agent)
    
    # Formulate request
    req_routing = A2ARoutingHeader(
        conversation_id=str(uuid.uuid4()),
        root_trace_id=str(uuid.uuid4()),
        sender_uri="urn:agent:devops_lead_01",
        recipient_uri="urn:agent:security_analyst_01"
    )
    req_payload = {"action": "scan_docker_image", "image_tag": "app:v1.4"}
    req_sec = A2ACryptoEngine.sign_payload(req_routing, req_payload)
    
    request_envelope = A2AMessageEnvelope(
        routing=req_routing,
        security=req_sec,
        intent="TASK_REQUEST",
        payload=req_payload
    )
    
    response = router.route_envelope(request_envelope)
    print("\n--- FINAL A2A EXCHANGE SUMMARY ---")
    print(f"Response Sender: {response.routing.sender_uri}")
    print(f"Verified Intent: {response.intent}")
    print(f"Payload: {response.payload}")
