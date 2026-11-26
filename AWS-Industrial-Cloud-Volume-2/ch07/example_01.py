#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: Post-Mortem Action Item Tracker & SLA Penalty Calculator
Author: Vatsal Shah
"""

import boto3
import json
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("PostMortemTracker")

class PostMortemAuditor:
    def __init__(self, dynamodb_table_name: str = "EnterprisePostMortemLedger"):
        self.dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
        self.table = self.dynamodb.Table(dynamodb_table_name)

    def calculate_sla_breach_cost(self, total_downtime_minutes: float, revenue_per_minute: float, agreed_sla_percent: float = 99.99) -> dict:
        """Calculates total financial SLA penalty and revenue loss."""
        total_month_minutes = 43200.0  # 30 days * 24h * 60m
        actual_uptime_percent = ((total_month_minutes - total_downtime_minutes) / total_month_minutes) * 100.0
        
        direct_revenue_lost = total_downtime_minutes * revenue_per_minute
        sla_penalty_percent = 0.0

        if actual_uptime_percent < 99.0:
            sla_penalty_percent = 50.0  # 50% SLA credit refund
        elif actual_uptime_percent < agreed_sla_percent:
            sla_penalty_percent = 25.0  # 25% SLA credit refund

        total_financial_impact = direct_revenue_lost * (1.0 + (sla_penalty_percent / 100.0))

        report = {
            "downtimeMinutes": total_downtime_minutes,
            "actualUptimePercent": round(actual_uptime_percent, 4),
            "agreedSlaPercent": agreed_sla_percent,
            "directRevenueLostUSD": round(direct_revenue_lost, 2),
            "slaPenaltyPercent": sla_penalty_percent,
            "totalFinancialLossUSD": round(total_financial_impact, 2)
        }
        logger.info(f"Financial Assessment: Total Loss = USD {report['totalFinancialLossUSD']}")
        return report

if __name__ == "__main__":
    auditor = PostMortemAuditor()
    auditor.calculate_sla_breach_cost(total_downtime_minutes=45.0, revenue_per_minute=5000.0, agreed_sla_percent=99.99)
