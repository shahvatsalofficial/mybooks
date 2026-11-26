#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: Multi-Service Observability Gap Auditor & EMF Metric Emitter
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
logger = logging.getLogger("ObservabilityAuditor")

class ObservabilityAuditor:
    def __init__(self, region_name: str = "us-east-1"):
        self.region = region_name
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.ecs_client = boto3.client('ecs', region_name=region_name)
        self.apigw_client = boto3.client('apigatewayv2', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)

    def audit_lambda_tracing(self) -> list:
        """Audits Lambda functions for active AWS X-Ray tracing configuration."""
        logger.info("Auditing AWS Lambda functions for X-Ray tracing...")
        gaps = []
        paginator = self.lambda_client.get_paginator('list_functions')

        for page in paginator.paginate():
            for fn in page.get('Functions', []):
                fn_name = fn['FunctionName']
                tracing_mode = fn.get('TracingConfig', {}).get('Mode', 'PassThrough')
                if tracing_mode != 'Active':
                    logger.warning(f"⚠️ Lambda Observability Gap: '{fn_name}' has TracingConfig='{tracing_mode}' (Expected: 'Active')")
                    gaps.append({"resourceType": "AWS::Lambda::Function", "name": fn_name, "gap": "TracingNotActive"})
                else:
                    logger.info(f"✅ Lambda '{fn_name}': X-Ray Active")
        return gaps

    def audit_ecs_container_insights(self) -> list:
        """Verifies CloudWatch Container Insights is enabled on all ECS clusters."""
        logger.info("Auditing ECS clusters for Container Insights...")
        gaps = []
        clusters = self.ecs_client.list_clusters().get('clusterArns', [])
        if not clusters:
            return gaps

        desc = self.ecs_client.describe_clusters(clusters=clusters, include=['SETTINGS'])
        for cl in desc.get('clusters', []):
            cl_name = cl['clusterName']
            settings = cl.get('settings', [])
            ci_enabled = any(s.get('name') == 'containerInsights' and s.get('value') == 'enabled' for s in settings)

            if not ci_enabled:
                logger.warning(f"⚠️ ECS Observability Gap: Cluster '{cl_name}' lacks Container Insights!")
                gaps.append({"resourceType": "AWS::ECS::Cluster", "name": cl_name, "gap": "ContainerInsightsDisabled"})
            else:
                logger.info(f"✅ ECS Cluster '{cl_name}': Container Insights Enabled")
        return gaps

    def emit_audit_metrics_emf(self, total_gaps: int):
        """Emits EMF structured log metric to stdout for asynchronous CloudWatch ingestion."""
        emf_payload = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": "Enterprise/ObservabilityGovernance",
                        "Dimensions": [["Region"]],
                        "Metrics": [
                            {"Name": "ObservabilityGapCount", "Unit": "Count"}
                        ]
                    }
                ]
            },
            "Region": self.region,
            "ObservabilityGapCount": total_gaps,
            "AuditTimestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }
        # Print directly to stdout for zero-overhead EMF extraction
        print(json.dumps(emf_payload))
        logger.info(f"Emitted EMF telemetry metric: ObservabilityGapCount = {total_gaps}")

if __name__ == "__main__":
    auditor = ObservabilityAuditor(region_name="us-east-1")
    lambda_gaps = auditor.audit_lambda_tracing()
    ecs_gaps = auditor.audit_ecs_container_insights()
    total = len(lambda_gaps) + len(ecs_gaps)
    logger.info(f"Audit Complete. Total Observability Gaps Identified: {total}")
    auditor.emit_audit_metrics_emf(total)
