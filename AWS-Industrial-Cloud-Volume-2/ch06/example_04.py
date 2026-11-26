#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: Automated FIS Chaos Experiment Runner & Steady-State Verifier
Author: Vatsal Shah
"""

import boto3
import time
import logging
import sys
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ChaosRunner")

class FisChaosController:
    def __init__(self, experiment_template_id: str, region_name: str = "us-east-1"):
        self.template_id = experiment_template_id
        self.region = region_name
        self.fis = boto3.client('fis', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)

    def start_experiment(self) -> str:
        """Launches the FIS Chaos Experiment."""
        logger.info(f"Starting AWS FIS Experiment from Template: {self.template_id}")
        try:
            response = self.fis.start_experiment(
                experimentTemplateId=self.template_id,
                tags={'Initiator': 'ContinuousResiliencePipeline', 'Environment': 'Staging'}
            )
            exp_id = response['experiment']['id']
            logger.info(f"✅ FIS Experiment launched successfully! ID: {exp_id}")
            return exp_id
        except ClientError as err:
            logger.error(f"Failed to start FIS experiment: {err.response['Error']['Message']}")
            return ""

    def verify_steady_state(self, alb_name: str, max_allowed_5xx_rate: float = 1.0) -> bool:
        """Queries CloudWatch metrics to ensure error rate does not breach SLA."""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(seconds=60)

        try:
            resp = self.cloudwatch.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'errors',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/ApplicationELB',
                                'MetricName': 'HTTPCode_Target_5XX_Count',
                                'Dimensions': [{'Name': 'LoadBalancer', 'Value': alb_name}]
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
                                'Dimensions': [{'Name': 'LoadBalancer', 'Value': alb_name}]
                            },
                            'Period': 60,
                            'Stat': 'Sum'
                        }
                    }
                ],
                StartTime=start_time,
                EndTime=now
            )
            errors = sum(resp['MetricDataResults'][0].get('Values', [0]))
            requests = sum(resp['MetricDataResults'][1].get('Values', [0]))

            error_rate = (errors / requests * 100.0) if requests > 0 else 0.0
            logger.info(f"Steady-State Check: Requests: {requests}, 5xx Errors: {errors} (Error Rate: {error_rate:.2f}%)")

            if error_rate > max_allowed_5xx_rate:
                logger.error(f"🚨 STEADY-STATE BREACH: Error rate {error_rate:.2f}% exceeds threshold {max_allowed_5xx_rate}%!")
                return False
            return True

        except ClientError as err:
            logger.warning(f"Error checking steady-state metrics: {err.response['Error']['Message']}")
            return True

    def monitor_and_enforce_safety(self, experiment_id: str, alb_name: str, duration_seconds: int = 300):
        """Monitors active experiment, executing manual abort if steady state is violated."""
        start_time = time.time()
        logger.info(f"Monitoring Chaos Experiment '{experiment_id}' for {duration_seconds}s...")

        while time.time() - start_time < duration_seconds:
            # Fetch experiment status
            exp_info = self.fis.get_experiment(id=experiment_id)['experiment']
            status = exp_info['state']['status']

            if status in ['completed', 'failed', 'stopped']:
                logger.info(f"FIS Experiment finished with terminal state: {status}")
                break

            # Validate system steady state
            if not self.verify_steady_state(alb_name=alb_name):
                logger.critical(f"Aborting FIS Experiment {experiment_id} due to resilience failure!")
                self.fis.stop_experiment(id=experiment_id)
                sys.exit(1)

            time.sleep(10)

        logger.info("✅ Resilience Verification Complete. System maintained steady-state under chaos!")

if __name__ == "__main__":
    TEMPLATE = "EXT1122334455"
    ALB = "app/prod-payment-alb/50dc6c495c0c9188"
    controller = FisChaosController(experiment_template_id=TEMPLATE)
    exp_id = controller.start_experiment()
    if exp_id:
        controller.monitor_and_enforce_safety(experiment_id=exp_id, alb_name=ALB)
