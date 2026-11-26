#!/usr/bin/env python3
"""
AWS Spot Fleet Price & Capacity Pool Optimization Engine
Author: Vatsal Shah / Enterprise Architecture Lab
License: Apache 2.0
"""

import boto3
import json
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SpotOptimizer")

INSTANCE_CANDIDATES = [
    "c7g.2xlarge", "m7g.2xlarge", "r7g.2xlarge",
    "c6g.2xlarge", "m6g.2xlarge",
    "c6i.2xlarge", "m6i.2xlarge"
]

class SpotPoolOptimizer:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.ec2 = boto3.client("ec2", region_name=region)

    def get_spot_price_history(self, instance_types: list) -> dict:
        """Retrieves Spot pricing history over the last 24 hours."""
        logger.info(f"Querying Spot pricing history in {self.region} for candidates...")
        start_time = datetime.utcnow() - timedelta(hours=24)
        
        response = self.ec2.describe_spot_price_history(
            InstanceTypes=instance_types,
            ProductDescriptions=["Linux/UNIX"],
            StartTime=start_time,
            MaxResults=100
        )
        
        pool_metrics = {}
        for item in response["SpotPriceHistory"]:
            key = f"{item['InstanceType']}:{item['AvailabilityZone']}"
            price = float(item["SpotPrice"])
            if key not in pool_metrics:
                pool_metrics[key] = []
            pool_metrics[key].append(price)
            
        summary = {}
        for pool, prices in pool_metrics.items():
            avg_price = sum(prices) / len(prices)
            inst_type, az = pool.split(":")
            summary[pool] = {
                "instance_type": inst_type,
                "az": az,
                "avg_spot_price": round(avg_price, 4),
                "stability_score": round(1.0 - (max(prices) - min(prices)) / avg_price, 3)
            }
        return summary

    def generate_launch_template_overrides(self, optimized_pools: dict) -> list:
        """Generates Launch Template override JSON blocks."""
        overrides = []
        seen_types = set()
        for pool_key, data in sorted(optimized_pools.items(), key=lambda x: x[1]["avg_spot_price"]):
            inst_type = data["instance_type"]
            if inst_type not in seen_types:
                seen_types.add(inst_type)
                # Assign weighted capacity (e.g., 2xlarge = 8 compute units)
                overrides.append({
                    "InstanceType": inst_type,
                    "WeightedCapacity": "8"
                })
        return overrides

if __name__ == "__main__":
    optimizer = SpotPoolOptimizer("us-east-1")
    pools = optimizer.get_spot_price_history(INSTANCE_CANDIDATES)
    overrides_config = optimizer.generate_launch_template_overrides(pools)
    
    print("\n" + "="*50)
    print("SPOT CAPACITY POOL OPTIMIZATION REPORT")
    print("="*50)
    print(f"Discovered {len(pools)} Independent Spot Capacity Pools.")
    print("\nRecommended ASG Mixed Instances Overrides:")
    print(json.dumps(overrides_config, indent=2))
