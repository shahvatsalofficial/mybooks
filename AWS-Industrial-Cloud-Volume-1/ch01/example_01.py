#!/usr/bin/env python3
"""
AWS Multi-Region Health & Latency Benchmarking Engine
Author: Vatsal Shah / Enterprise Cloud Architecture Lab
License: Apache 2.0
"""

import time
import json
import logging
import urllib.request
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MultiRegionProber")

REGIONS_TO_MONITOR = [
    {"region_name": "us-east-1", "az_id": "use1-az1", "api_endpoint": "https://api-us-east-1.enterprise.com/health"},
    {"region_name": "us-west-2", "az_id": "usw2-az1", "api_endpoint": "https://api-us-west-2.enterprise.com/health"},
    {"region_name": "eu-west-1", "az_id": "euw1-az1", "api_endpoint": "https://api-eu-west-1.enterprise.com/health"},
    {"region_name": "ap-southeast-1", "az_id": "apse1-az1", "api_endpoint": "https://api-ap-southeast-1.enterprise.com/health"}
]

class MultiRegionHealthProber:
    def __init__(self, regions_config):
        self.regions = regions_config
        self.cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

    def probe_http_endpoint(self, url: str) -> dict:
        """Measures TCP connect, TLS handshake, and TTFB latency."""
        start_time = time.perf_counter()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AWS-Enterprise-Prober/2.0"})
            with urllib.request.urlopen(req, timeout=5.0) as response:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                status_code = response.getcode()
                return {"healthy": status_code == 200, "latency_ms": round(latency_ms, 2), "status_code": status_code}
        except Exception as err:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return {"healthy": False, "latency_ms": round(latency_ms, 2), "error": str(err)}

    def check_aurora_replication_lag(self, region_name: str, db_cluster_id: str) -> float:
        """Queries CloudWatch metrics for Aurora Global DB replication lag."""
        try:
            cw = boto3.client("cloudwatch", region_name=region_name)
            response = cw.get_metric_data(
                MetricDataQueries=[
                    {
                        "Id": "rep_lag",
                        "MetricStat": {
                            "Metric": {
                                "Namespace": "AWS/RDS",
                                "MetricName": "AuroraGlobalDBReplicationLag",
                                "Dimensions": [{"Name": "DBClusterIdentifier", "Value": db_cluster_id}]
                            },
                            "Period": 60,
                            "Stat": "Average"
                        }
                    }
                ],
                StartTime=time.time() - 300,
                EndTime=time.time()
            )
            values = response["MetricDataResults"][0]["Values"]
            return round(values[0], 2) if values else 0.0
        except ClientError:
            return 0.0

    def publish_cloudwatch_telemetry(self, region: str, latency: float, healthy: bool):
        """Pushes custom health metrics to AWS CloudWatch."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace="Enterprise/GlobalInfrastructure",
                MetricData=[
                    {
                        "MetricName": "EdgeLatencyMs",
                        "Dimensions": [{"Name": "TargetRegion", "Value": region}],
                        "Value": latency,
                        "Unit": "Milliseconds"
                    },
                    {
                        "MetricName": "RegionalHealthStatus",
                        "Dimensions": [{"Name": "TargetRegion", "Value": region}],
                        "Value": 1.0 if healthy else 0.0,
                        "Unit": "Count"
                    }
                ]
            )
        except ClientError as err:
            logger.error(f"Failed to publish CloudWatch metric: {err}")

    def execute_probe_cycle(self):
        """Executes a full health check cycle across all configured regions."""
        logger.info("Starting Global Infrastructure Multi-Region Probe Cycle...")
        results = []
        for target in self.regions:
            probe_result = self.probe_http_endpoint(target["api_endpoint"])
            self.publish_cloudwatch_telemetry(target["region_name"], probe_result["latency_ms"], probe_result["healthy"])
            
            summary = {
                "region": target["region_name"],
                "az_id": target["az_id"],
                "status": "HEALTHY" if probe_result["healthy"] else "DEGRADED",
                "latency_ms": probe_result["latency_ms"]
            }
            results.append(summary)
            logger.info(f"Region: {summary['region']} [{summary['az_id']}] -> Status: {summary['status']} ({summary['latency_ms']} ms)")
        
        return results

if __name__ == "__main__":
    prober = MultiRegionHealthProber(REGIONS_TO_MONITOR)
    report = prober.execute_probe_cycle()
    print("\n" + "="*50)
    print("GLOBAL INFRASTRUCTURE TELEMETRY AUDIT REPORT")
    print("="*50)
    print(json.dumps(report, indent=2))
