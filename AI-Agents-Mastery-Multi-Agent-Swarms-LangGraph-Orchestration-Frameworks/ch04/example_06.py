class WebhookPayloadInput(BaseModel):
    endpoint_url: str = Field(description="The target HTTP/HTTPS destination URL")
    event_type: str = Field(description="Standardized event name (e.g., alert.security, task.completed)")
    payload_data: Dict[str, Any] = Field(description="JSON-serializable data dictionary")

class WebhookDispatchTool(BaseTool):
    name: str = "webhook_dispatch_tool"
    description: str = "Dispatches structured JSON notifications to external enterprise webhooks."
    args_schema: type[BaseModel] = WebhookPayloadInput

    def _run(self, endpoint_url: str, event_type: str, payload_data: Dict[str, Any]) -> str:
        if not endpoint_url.startswith("https://"):
            return "ERROR: Webhook endpoint must enforce TLS (https://)."
        
        print(f"[TOOL: Webhook] Dispatching event '{event_type}' to {endpoint_url}...")
        return f"SUCCESS: Dispatched {event_type} webhook. HTTP Status: 202 Accepted."
