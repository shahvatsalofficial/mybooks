#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: Idempotent Event Processing with Lambda Powertools & DynamoDB
Author: Vatsal Shah
"""

import json
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent_function
)

logger = Logger(service="PaymentProcessor")

# Configure DynamoDB persistence layer with 1-hour expiration
persistence_layer = DynamoDBPersistenceLayer(
    table_name="serverless_idempotency_store",
    key_attr="idempotency_key",
    expiry_attr="expires_at",
    status_attr="status",
    in_progress_expiry_attr="in_progress_expires_at"
)

idempotency_config = IdempotencyConfig(
    event_key_jmespath="body.transactionId",
    use_local_cache=True,
    max_local_cache_size=1000
)

@idempotent_function(data_keyword_argument="payload", config=idempotency_config, persistence_store=persistence_layer)
def execute_payment(payload: dict) -> dict:
    """Executes non-idempotent credit card charge against external gateway."""
    tx_id = payload.get("transactionId")
    amt = payload.get("amount")
    logger.info(f"Processing payment for Transaction: {tx_id}, Amount: " + str(amt))
    
    # Simulate payment settlement
    return {
        "status": "SETTLED",
        "transactionId": tx_id,
        "amount": amt,
        "authCode": "AUTH_987654321"
    }

def lambda_handler(event, context):
    logger.info("Received payment event", extra={"event": event})
    body = json.loads(event.get("body", "{}"))
    
    try:
        result = execute_payment(payload=body)
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
    except Exception as err:
        logger.error(f"Payment execution failed: {str(err)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(err)})
        }
