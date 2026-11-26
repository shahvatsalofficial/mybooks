class StreamingTokenDispatcher:
    def __init__(self):
        self.is_inside_tool_payload = False

    def process_token(self, token: str) -> Optional[str]:
        # If token begins an action block, suppress from customer UI
        if "Action:" in token:
            self.is_inside_tool_payload = True
            return "[System: Executing verification tool...]"
            
        if "Observation:" in token or "Final Answer:" in token:
            self.is_inside_tool_payload = False
            if "Final Answer:" in token:
                return "
"
            return None

        if not self.is_inside_tool_payload:
            return token
        return None

# Verification
dispatcher = StreamingTokenDispatcher()
stream = ["Thought: ", "Let ", "me ", "check. ", "Action: query() ", "Observation: ok ", "Final Answer: ", "Your ", "order ", "shipped."]
client_ui = []
for tok in stream:
    out = dispatcher.process_token(tok)
    if out:
        client_ui.append(out)
print("Client UI Rendered Stream:", "".join(client_ui))
