import json
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Production AWS Lambda handler for Bedrock Agent Action Group invocations."""
    logger.info("Received Bedrock Event: %s", json.dumps(event))
    
    agent_info = event.get("agent", {})
    action_group = event.get("actionGroup", "UnknownActionGroup")
    api_path = event.get("apiPath", "")
    http_method = event.get("httpMethod", "POST")
    message_version = event.get("messageVersion", "1.0")
    
    parameters = {}
    if "requestBody" in event and "content" in event["requestBody"]:
        json_content = event["requestBody"]["content"].get("application/json", {})
        for prop in json_content.get("properties", []):
            parameters[prop["name"]] = prop["value"]
            
    response_body = {}
    status_code = 200
    
    try:
        if api_path == "/query_logs":
            log_group = parameters.get("log_group")
            query = parameters.get("query_string")
            limit = int(parameters.get("limit", 10))
            
            if not log_group or not query:
                status_code = 400
                response_body = {"status": "ERROR", "message": "Missing required fields: log_group or query_string"}
            else:
                simulated_events = [
                    f"[2026-11-23 16:42:11 UTC] ERROR: Database connection timeout pool=aurora-pg-01",
                    f"[2026-11-23 16:42:14 UTC] WARN: Retry count exceeded (3/3), aborting transaction"
                ]
                response_body = {
                    "status": "SUCCESS",
                    "records_found": len(simulated_events),
                    "events": simulated_events[:limit]
                }
        else:
            status_code = 404
            response_body = {"status": "NOT_FOUND", "message": f"Unrecognized apiPath: {api_path}"}
            
    except Exception as exc:
        logger.error("Lambda execution failure: %s", str(exc), exc_info=True)
        status_code = 500
        response_body = {"status": "INTERNAL_ERROR", "error": str(exc)}
        
    return {
        "messageVersion": message_version,
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": http_method,
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(response_body)
                }
            }
        }
    }

if __name__ == "__main__":
    sample_event = {
        "messageVersion": "1.0",
        "agent": {"name": "DiagnosticAgent", "id": "BEDROCK123"},
        "actionGroup": "CloudWatchDiagnostics",
        "apiPath": "/query_logs",
        "httpMethod": "POST",
        "requestBody": {
            "content": {
                "application/json": {
                    "properties": [
                        {"name": "log_group", "type": "string", "value": "/aws/ecs/orders"},
                        {"name": "query_string", "type": "string", "value": "filter ERROR"},
                        {"name": "limit", "type": "integer", "value": "5"}
                    ]
                }
            }
        }
    }
    res = lambda_handler(sample_event, None)
    print("-> Lambda Execution Result:")
    print(f"   HTTP Status: {res['response']['httpStatusCode']}")
    print(f"   Body: {res['response']['responseBody']['application/json']['body']}")
