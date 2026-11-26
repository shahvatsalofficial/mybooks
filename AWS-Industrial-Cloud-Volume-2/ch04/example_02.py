# lambda_sqs_batch_consumer.py - Production Partial Batch Failure Handler
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    batch_item_failures = []
    records = event.get('Records', [])

    for record in records:
        message_id = record['messageId']
        try:
            body = json.loads(record['body'])
            process_transaction(body)
            logger.info(f"Successfully processed message: {message_id}")
        except Exception as err:
            logger.error(f"Failed to process message {message_id}: {str(err)}")
            # Mark this specific message as failed
            batch_item_failures.append({"itemIdentifier": message_id})

    # Return structured failure list to SQS event source mapping
    return {"batchItemFailures": batch_item_failures}

def process_transaction(data: dict):
    if "accountId" not in data:
        raise ValueError("Invalid payload: Missing accountId")
    # Business logic execution...
