import asyncio

async def stream_agent_execution(graph_runnable: Any, input_data: Dict[str, Any], thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    print(f"\n[STREAM] Initiating real-time event stream for Thread: {thread_id}...")
    
    async for event in graph_runnable.astream_events(input_data, config=config, version="v2"):
        event_kind = event["event"]
        node_name = event.get("metadata", {}).get("langgraph_node", "orchestrator")
        
        # 1. Stream raw LLM tokens as they are generated
        if event_kind == "on_chat_model_stream":
            chunk_content = event["data"]["chunk"].content
            if chunk_content:
                print(chunk_content, end="", flush=True)
                
        # 2. Capture node lifecycle boundaries
        elif event_kind == "on_chain_start" and node_name != "orchestrator":
            print(f"\n>>> [NODE START]: {node_name}")
            
        elif event_kind == "on_chain_end" and node_name != "orchestrator":
            print(f"\n<<< [NODE END]: {node_name}")
