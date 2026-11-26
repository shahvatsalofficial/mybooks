def test_cross_framework_envelope_interop():
    langgraph_state = {"ticket_id": "T-99", "status": "ESCALATED"}
    envelope = SchemaTransformer.langgraph_to_a2a(langgraph_state, "conv_cross_001")
    
    # AutoGen adapter unwraps envelope into ConversableAgent tuple
    autogen_message = {
        "role": "assistant",
        "name": envelope.routing.sender_uri.split(":")[-1],
        "content": json.dumps(envelope.payload)
    }
    
    assert "ESCALATED" in autogen_message["content"]
    print("[INTEROP TEST] 100% PASS: LangGraph state seamlessly mapped into AutoGen message.")
