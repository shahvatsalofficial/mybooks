"""
Recipe 02.1: Production Bedrock Agent Action Group Lambda Handler.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

# Configure structured JSON logging for Amazon CloudWatch Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class TradeDetailsRequest(BaseModel):
    """Pydantic v2 schema for GET /trades/{trade_id} parameter validation."""
    trade_id: str = Field(..., pattern=r"^TX-[0-9]{4,8}$", description="Trade identifier matching TX-XXXXX")


class TradeExecutionRecord(BaseModel):
    trade_id: str
    symbol: str
    quantity: int
    price: float
    status: str
    counterparty: str
    settlement_timestamp: str


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler invoked synchronously by Amazon Bedrock Agent.
    Strictly validates input parameters and enforces the Bedrock response envelope.
    """
    logger.info(f"Received Bedrock Agent Action Group Event: {json.dumps(event)}")

    # Extract top-level Bedrock metadata
    action_group = event.get("actionGroup", "")
    api_path = event.get("apiPath", "")
    http_method = event.get("httpMethod", "")
    message_version = event.get("messageVersion", "1.0")

    # Map raw parameters list to an internal key-value dictionary
    raw_params = event.get("parameters", [])
    param_dict = {p.get("name"): p.get("value") for p in raw_params if "name" in p}

    try:
        # Route: GET /trades/{trade_id}
        if api_path == "/trades/{trade_id}" and http_method.upper() == "GET":
            # Validate input parameter against Pydantic schema
            validated_input = TradeDetailsRequest(trade_id=param_dict.get("trade_id", ""))
            
            # Execute business logic (e.g., query database or ledger)
            record = _fetch_trade_from_database(validated_input.trade_id)
            
            response_body_content = record.model_dump_json()
            status_code = 200

        else:
            logger.warning(f"Unrecognized API path [{api_path}] or method [{http_method}]")
            response_body_content = json.dumps({"error": f"Path '{api_path}' with method '{http_method}' not found."})
            status_code = 404

    except ValidationError as ve:
        logger.error(f"Parameter validation failed: {ve.json()}")
        response_body_content = json.dumps({"error": "SchemaValidationError", "details": ve.errors()})
        status_code = 400

    except Exception as e:
        logger.exception(f"Unexpected operational failure: {str(e)}")
        response_body_content = json.dumps({"error": "InternalServerError", "message": "Failed to reconcile trade."})
        status_code = 500

    # Build the mandatory Amazon Bedrock Agent response structure
    bedrock_response_envelope = {
        "messageVersion": message_version,
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": http_method,
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": response_body_content
                }
            }
        },
        # Session attributes can be mutated and returned to Claude's memory
        "sessionAttributes": event.get("sessionAttributes", {}),
        "promptSessionAttributes": event.get("promptSessionAttributes", {})
    }

    logger.info(f"Returning Bedrock Response Envelope [Status {status_code}]")
    return bedrock_response_envelope


def _fetch_trade_from_database(trade_id: str) -> TradeExecutionRecord:
    """Mock database lookup with verified return structure."""
    return TradeExecutionRecord(
        trade_id=trade_id,
        symbol="NVDA",
        quantity=5000,
        price=138.45,
        status="SETTLED",
        counterparty="Goldman_Sachs_Clearing",
        settlement_timestamp="2026-10-02T14:32:00Z"
    )
