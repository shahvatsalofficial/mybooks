def consolidate_tool_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    consolidated = []
    tool_buffer = []
    
    for msg in messages:
        if msg["role"] == "tool":
            tool_buffer.append(f"- {msg['content'].strip()}")
        else:
            if tool_buffer:
                consolidated.append({
                    "role": "tool",
                    "content": "Consolidated Observations:\n" + "\n".join(tool_buffer)
                })
                tool_buffer.clear()
            consolidated.append(msg)
            
    if tool_buffer:
        consolidated.append({
            "role": "tool",
            "content": "Consolidated Observations:\n" + "\n".join(tool_buffer)
        })
    return consolidated
