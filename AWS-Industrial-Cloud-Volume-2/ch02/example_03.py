#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: Real-Time Blue/Green Deployment Health Monitor & Rollback Trigger
Author: Vatsal Shah
"""

import boto3
import time
import sys
import logging
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("DeploymentMonitor")

class BlueGreenDeploymentGuard:
    def __init__(self, application_name: str, deployment_group: str, region_name: str = "us-east-1"):
        self.app_name = application_name
        self.dg_name = deployment_group
        self.region = region_name
        self.codedeploy = boto3.client('codedeploy', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.ecs = boto3.client('ecs', region_name=region_name)

    def get_latest_deployment_id(self) -> str:
        """Retrieves the ID of the currently in-progress or most recent deployment."""
        try:
            response = self.codedeploy.list_deployments(
                applicationName=self.app_name,
                deploymentGroupName=self.dg_name,
                includeOnlyStatuses=['InProgress', 'Created', 'Queued']
            )
            deployments = response.get('deployments', [])
            if not deployments:
                logger.info("No active deployments currently in progress.")
                return ""
            return deployments[0]
        except ClientError as err:
            logger.error(f"Failed to list deployments: {err.response['Error']['Message']}")
            return ""

    def evaluate_error_rate(self, alb_name: str, target_group_arn: str, lookback_seconds: int = 60) -> float:
        """Calculates the 5xx error percentage over the lookback window."""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(seconds=lookback_seconds)

        try:
            # Query HTTPCode_Target_5XX_Count
            response_5xx = self.cloudwatch.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'errors',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/ApplicationELB',
                                'MetricName': 'HTTPCode_Target_5XX_Count',
                                'Dimensions': [
                                    {'Name': 'TargetGroup', 'Value': target_group_arn.split('/')[-2] + '/' + target_group_arn.split('/')[-1]},
                                    {'Name': 'LoadBalancer', 'Value': alb_name}
                                ]
                            },
                            'Period': 60,
                            'Stat': 'Sum'
                        }
                    },
                    {
                        'Id': 'requests',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/ApplicationELB',
                                'MetricName': 'RequestCount',
                                'Dimensions': [
                                    {'Name': 'TargetGroup', 'Value': target_group_arn.split('/')[-2] + '/' + target_group_arn.split('/')[-1]},
                                    {'Name': 'LoadBalancer', 'Value': alb_name}
                                ]
                            },
                            'Period': 60,
                            'Stat': 'Sum'
                        }
                    }
                ],
                StartTime=start_time,
                EndTime=now
            )

            error_values = response_5xx['MetricDataResults'][0].get('Values', [0])
            request_values = response_5xx['MetricDataResults'][1].get('Values', [0])

            total_errors = sum(error_values)
            total_requests = sum(request_values)

            if total_requests == 0:
                return 0.0

            error_rate = (total_errors / total_requests) * 100.0
            return error_rate

        except ClientError as err:
            logger.warning(f"Error querying CloudWatch metrics: {err.response['Error']['Message']}")
            return 0.0

    def trigger_instant_rollback(self, deployment_id: str, reason: str):
        """Executes an emergency stop and rollback on the active CodeDeploy deployment."""
        logger.critical(f"🚨 INITIATING EMERGENCY ROLLBACK for {deployment_id}! Reason: {reason}")
        try:
            self.codedeploy.stop_deployment(
                deploymentId=deployment_id,
                autoRollbackEnabled=True
            )
            logger.info("✅ Stop and rollback command successfully issued to CodeDeploy.")
        except ClientError as err:
            logger.error(f"❌ Failed to stop deployment: {err.response['Error']['Message']}")

    def monitor_loop(self, alb_name: str, green_tg_arn: str, max_error_rate_pct: float = 1.0, poll_interval: int = 10):
        """Continuous monitoring loop during deployment."""
        deployment_id = self.get_latest_deployment_id()
        if not deployment_id:
            return

        logger.info(f"Starting real-time health guard for Deployment: {deployment_id}")

        while True:
            dep_info = self.codedeploy.get_deployment(deploymentId=deployment_id)['deploymentInfo']
            status = dep_info['status']

            if status in ['Succeeded', 'Failed', 'Stopped']:
                logger.info(f"Deployment reached terminal status: {status}. Exiting monitor.")
                break

            current_error_rate = self.evaluate_error_rate(alb_name, green_tg_arn)
            logger.info(f"[Deployment {deployment_id}] Status: {status} | Green TG 5xx Error Rate: {current_error_rate:.2f}%")

            if current_error_rate > max_error_rate_pct:
                self.trigger_instant_rollback(
                    deployment_id,
                    f"5xx error rate ({current_error_rate:.2f}%) exceeded threshold ({max_error_rate_pct}%)"
                )
                break

            time.sleep(poll_interval)

if __name__ == "__main__":
    guard = BlueGreenDeploymentGuard(
        application_name="enterprise-payment-service",
        deployment_group="production-bluegreen-dg"
    )
    # Target ALB & Green Target Group ARN
    ALB_NAME = "app/prod-payment-alb/50dc6c495c0c9188"
    GREEN_TG = "targetgroup/prod-payment-green/73e2d6f24d661a15"
    guard.monitor_loop(alb_name=ALB_NAME, green_tg_arn=GREEN_TG, max_error_rate_pct=1.0)
