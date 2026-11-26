from typing import Dict, Any
import json

class AgentBuilderWebhookHandler:
    """Parses and answers Vertex AI Agent Builder fulfillment webhooks."""

    @staticmethod
    def handle_fulfillment(request_payload: Dict[str, Any]) -> Dict[str, Any]:
        tag = request_payload.get("fulfillmentInfo", {}).get("tag")
        session_info = request_payload.get("sessionInfo", {})
        parameters = session_info.get("parameters", {})
        
        if tag == "check_service_health":
            svc_name = parameters.get("service_name", "unknown")
            return {
                "fulfillmentResponse": {
                    "messages": [
                        {"text": {"text": [f"Service '{svc_name}' reports all 12 replicas healthy in us-central1."]}}
                    ]
                },
                "sessionInfo": {
                    "parameters": {"service_status": "OPTIMAL"}
                }
            }
        
        return {
            "fulfillmentResponse": {
                "messages": [{"text": {"text": ["Unrecognized fulfillment tag."]}}]
            }
        }

if __name__ == "__main__":
    payload = {
        "fulfillmentInfo": {"tag": "check_service_health"},
        "sessionInfo": {"parameters": {"service_name": "payments"}}
    }
    resp = AgentBuilderWebhookHandler.handle_fulfillment(payload)
    print("Webhook Response:", json.dumps(resp, indent=2))
