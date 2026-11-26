"""
Recipe 06.3: DynamoDB Departmental Token Metering & Budget Governor.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import time
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.config import Config
from pydantic import BaseModel

logger = logging.getLogger("FinOpsMeterGovernor")
logger.setLevel(logging.INFO)


class BudgetExceededException(Exception):
    """Raised when a tenant cost center has exceeded its monthly spending ceiling."""
    pass


class DepartmentUsageRecord(BaseModel):
    cost_center: str
    department: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cost_usd: float
    request_id: str


class DynamoDBFinOpsGovernor:
    """
    Enforces departmental token quotas and writes atomic usage items to DynamoDB.
    """

    def __init__(self, table_name: str = "FinOpsMeterLedger", region_name: str = "us-east-1"):
        config = Config(region_name=region_name, retries={"max_attempts": 3, "mode": "adaptive"})
        self.dynamodb = boto3.resource("dynamodb", config=config)
        self.table = self.dynamodb.Table(table_name)
        # Default departmental monthly budget allocations (in USD)
        self.monthly_budgets = {
            "CC-FIN-9021": 25000.00, # Institutional Equities
            "CC-RISK-4402": 15000.00, # Risk Analytics
            "CC-LEGAL-1105": 8000.00, # Corporate Legal
        }

    def verify_budget_headroom(self, cost_center: str) -> float:
        """
        Queries MTD spend partition. Raises BudgetExceededException if budget breached.
        """
        current_month = time.strftime("%Y-%m")
        pk = f"MTD#{cost_center}#{current_month}"
        
        try:
            response = self.table.get_item(Key={"PK": pk, "SK": "SUMMARY"})
            item = response.get("Item", {})
            current_spend = float(item.get("mtd_spend_usd", 0.0))
            budget_limit = self.monthly_budgets.get(cost_center, 5000.00)

            if current_spend >= budget_limit:
                logger.error(f"Cost Center [{cost_center}] breached monthly budget (${current_spend:.2f} >= ${budget_limit:.2f})")
                raise BudgetExceededException(f"Budget exceeded for {cost_center}. Spending ceiling: ${budget_limit:.2f}")

            remaining = budget_limit - current_spend
            logger.info(f"Cost Center [{cost_center}] approved. Headroom remaining: ${remaining:.2f}")
            return remaining
        except BudgetExceededException:
            raise
        except Exception as e:
            logger.warning(f"Failed to query DynamoDB budget summary: {str(e)}. Permitting execution.")
            return 1000.00

    def record_transaction_usage(self, record: DepartmentUsageRecord) -> None:
        """
        Atomically records itemized transaction and updates the MTD summary partition.
        """
        current_epoch = int(time.time())
        current_month = time.strftime("%Y-%m")
        ttl = current_epoch + (86400 * 90) # 90-day retention

        # 1. Write itemized transaction record
        self.table.put_item(
            Item={
                "PK": f"TRANSACTION#{record.cost_center}",
                "SK": f"REQ#{current_epoch}#{record.request_id}",
                "cost_center": record.cost_center,
                "department": record.department,
                "input_tokens": record.input_tokens,
                "output_tokens": record.output_tokens,
                "cache_read_tokens": record.cache_read_tokens,
                "cost_usd": str(record.cost_usd),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "ttl": ttl
            }
        )

        # 2. Atomically increment MTD aggregate summary partition
        summary_pk = f"MTD#{record.cost_center}#{current_month}"
        self.table.update_item(
            Key={"PK": summary_pk, "SK": "SUMMARY"},
            UpdateExpression="ADD mtd_spend_usd :cost, total_requests :one",
            ExpressionAttributeValues={
                ":cost": round(record.cost_usd, 6),
                ":one": 1
            }
        )
        logger.info(f"Recorded usage for [{record.cost_center}]: ${record.cost_usd:.4f} added to MTD ledger.")
