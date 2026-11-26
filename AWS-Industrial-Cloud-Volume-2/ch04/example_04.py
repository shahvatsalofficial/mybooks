#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: SQS Dead Letter Queue Redrive & Poison Pill Quarantine Engine
Author: Vatsal Shah
"""

import boto3
import json
import logging
import sys
import time
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("DlqRedriveEngine")

class SqsDlqManager:
    def __init__(self, primary_queue_url: str, dlq_url: str, region_name: str = "us-east-1"):
        self.primary_url = primary_queue_url
        self.dlq_url = dlq_url
        self.region = region_name
        self.sqs = boto3.client('sqs', region_name=region_name)

    def get_queue_attributes(self, queue_url: str) -> dict:
        """Retrieves real-time message count attributes."""
        try:
            response = self.sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'QueueArn']
            )
            return response.get('Attributes', {})
        except ClientError as err:
            logger.error(f"Failed to fetch queue attributes: {err.response['Error']['Message']}")
            return {}

    def audit_and_quarantine_poison_pills(self, quarantine_file: str = "poison_pills.json", max_messages: int = 100):
        """Scans DLQ for non-parseable JSON or corrupt messages, isolating them to disk."""
        logger.info(f"Auditing Dead Letter Queue: {self.dlq_url}")
        quarantined = []

        try:
            response = self.sqs.receive_message(
                QueueUrl=self.dlq_url,
                MaxNumberOfMessages=min(max_messages, 10),
                VisibilityTimeout=30,
                WaitTimeSeconds=5
            )
            messages = response.get('Messages', [])
            logger.info(f"Received {len(messages)} message(s) from DLQ for inspection.")

            for msg in messages:
                receipt_handle = msg['ReceiptHandle']
                body_raw = msg['Body']
                is_poison = False
                reason = ""

                try:
                    payload = json.loads(body_raw)
                    if "accountId" not in payload:
                        is_poison = True
                        reason = "Missing required 'accountId' schema key"
                except json.JSONDecodeError as json_err:
                    is_poison = True
                    reason = f"Corrupt JSON payload: {str(json_err)}"

                if is_poison:
                    logger.warning(f"🚨 POISON PILL DETECTED [ID: {msg['MessageId']}]: {reason}")
                    quarantined.append({
                        "messageId": msg['MessageId'],
                        "body": body_raw,
                        "quarantineReason": reason,
                        "timestamp": time.time()
                    })
                    # Delete from DLQ to prevent re-redriving poison message
                    self.sqs.delete_message(QueueUrl=self.dlq_url, ReceiptHandle=receipt_handle)

            if quarantined:
                with open(quarantine_file, 'w') as f:
                    json.dump(quarantined, f, indent=2)
                logger.info(f"Saved {len(quarantined)} poison pills to '{quarantine_file}'.")

        except ClientError as err:
            logger.error(f"Error during poison pill audit: {err.response['Error']['Message']}")

    def start_automated_redrive(self):
        """Initiates high-throughput SQS StartMessageMoveTask API."""
        dlq_attrs = self.get_queue_attributes(self.dlq_url)
        primary_attrs = self.get_queue_attributes(self.primary_url)

        dlq_arn = dlq_attrs.get('QueueArn')
        primary_arn = primary_attrs.get('QueueArn')
        msg_count = int(dlq_attrs.get('ApproximateNumberOfMessages', 0))

        if msg_count == 0:
            logger.info("DLQ is empty. No redrive task required.")
            return

        logger.info(f"Initiating AWS SQS MessageMoveTask: {msg_count} messages -> {primary_arn}")

        try:
            response = self.sqs.start_message_move_task(
                SourceArn=dlq_arn,
                DestinationArn=primary_arn
            )
            task_handle = response.get('TaskHandle')
            logger.info(f"✅ SQS Redrive Task successfully started. Handle: {task_handle}")

            # Monitor progress
            while True:
                status_resp = self.sqs.list_message_move_tasks(SourceArn=dlq_arn)
                tasks = status_resp.get('Results', [])
                if not tasks:
                    break
                task = tasks[0]
                status = task.get('Status')
                moved = task.get('ApproximateNumberOfMessagesMoved', 0)
                logger.info(f"[Task {task_handle}] Status: {status} | Messages Moved: {moved}/{msg_count}")

                if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                    break
                time.sleep(5)

        except ClientError as err:
            logger.error(f"Failed to execute SQS redrive task: {err.response['Error']['Message']}")

if __name__ == "__main__":
    PRIMARY = "https://sqs.us-east-1.amazonaws.com/112233445566/production-orders.fifo"
    DLQ = "https://sqs.us-east-1.amazonaws.com/112233445566/production-orders-dlq.fifo"
    
    manager = SqsDlqManager(primary_queue_url=PRIMARY, dlq_url=DLQ)
    manager.audit_and_quarantine_poison_pills()
    manager.start_automated_redrive()
