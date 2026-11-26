#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: Multi-VPC Pod IP Exhaustion Auditor & Prefix Delegation Verifier
Author: Vatsal Shah
"""

import boto3
import json
import logging
import sys
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("PodIpAuditor")

class EksSubnetIpAuditor:
    def __init__(self, cluster_name: str, region_name: str = "us-east-1"):
        self.cluster_name = cluster_name
        self.region = region_name
        self.ec2 = boto3.client('ec2', region_name=region_name)
        self.eks = boto3.client('eks', region_name=region_name)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)

    def get_cluster_subnets(self) -> list:
        """Fetches all subnets associated with the EKS cluster."""
        try:
            response = self.eks.describe_cluster(name=self.cluster_name)
            resources_vpc = response['cluster']['resourcesVpcConfig']
            subnet_ids = resources_vpc.get('subnetIds', [])
            logger.info(f"Discovered {len(subnet_ids)} core subnet(s) for cluster '{self.cluster_name}'.")
            return subnet_ids
        except ClientError as err:
            logger.error(f"Failed to describe EKS cluster: {err.response['Error']['Message']}")
            return []

    def audit_subnet_capacity(self, critical_threshold_pct: float = 15.0) -> list:
        """Audits available IPv4 addresses and prefix blocks across subnets."""
        subnets = self.get_cluster_subnets()
        if not subnets:
            return []

        try:
            response = self.ec2.describe_subnets(SubnetIds=subnets)
            subnet_details = response.get('Subnets', [])
            exhausted_subnets = []

            logger.info(f"{'='*90}")
            logger.info(f"{'SUBNET ID':<24} | {'AZ':<12} | {'CIDR BLOCK':<18} | {'FREE IPS':<10} | {'STATUS'}")
            logger.info(f"{'='*90}")

            for sn in subnet_details:
                subnet_id = sn['SubnetId']
                az = sn['AvailabilityZone']
                cidr = sn['CidrBlock']
                free_ips = sn['AvailableIpAddressCount']

                # Calculate total IPs based on CIDR mask
                mask = int(cidr.split('/')[-1])
                total_ips = 2 ** (32 - mask) - 5  # Subtract 5 AWS reserved IPs
                pct_free = (free_ips / total_ips) * 100.0 if total_ips > 0 else 0

                if pct_free < critical_threshold_pct:
                    status = "CRITICAL / LOW IP"
                    exhausted_subnets.append(sn)
                else:
                    status = "HEALTHY"

                logger.info(f"{subnet_id:<24} | {az:<12} | {cidr:<18} | {free_ips:<10} | {status} ({pct_free:.1f}%)")

            logger.info(f"{'='*90}")
            logger.info(f"Audit Complete: {len(exhausted_subnets)} subnet(s) below {critical_threshold_pct}% threshold.")

            if exhausted_subnets:
                self.publish_cloudwatch_alarm(len(exhausted_subnets))

            return exhausted_subnets

        except ClientError as err:
            logger.error(f"Error querying EC2 subnets: {err.response['Error']['Message']}")
            return []

    def publish_cloudwatch_alarm(self, exhausted_count: int):
        """Pushes metric to CloudWatch for PagerDuty alerting."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace="Enterprise/EKS/Networking",
                MetricData=[
                    {
                        'MetricName': 'ExhaustedSubnetCount',
                        'Dimensions': [{'Name': 'ClusterName', 'Value': self.cluster_name}],
                        'Value': exhausted_count,
                        'Unit': 'Count'
                    }
                ]
            )
            logger.warning(f"🚨 Published CloudWatch alarm metric: {exhausted_count} exhausted subnet(s).")
        except ClientError as err:
            logger.error(f"Failed to publish CloudWatch metric: {err.response['Error']['Message']}")

if __name__ == "__main__":
    CLUSTER = "industrial-eks-prod"
    auditor = EksSubnetIpAuditor(cluster_name=CLUSTER)
    auditor.audit_subnet_capacity(critical_threshold_pct=20.0)
