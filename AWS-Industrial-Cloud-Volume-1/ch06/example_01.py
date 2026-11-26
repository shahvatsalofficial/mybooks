#!/usr/bin/env python3
"""
AWS Multi-Region Database Sovereignty & Replication Monitor
Author: Vatsal Shah / Enterprise Data Systems Engineering
License: Apache 2.0
"""

import boto3
import json
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DatabaseMonitor")

class GlobalDatabaseMonitor:
    def __init__(self, global_cluster_id: str, ddb_table_name: str):
        self.global_cluster_id = global_cluster_id
        self.ddb_table_name = ddb_table_name
        self.rds = boto3.client("rds", region_name="us-east-1")
        self.ddb = boto3.client("dynamodb", region_name="us-east-1")

    def audit_aurora_global_cluster(self) -> dict:
        """Inspects Aurora Global Database topology and failover state."""
        logger.info(f"Auditing Aurora Global Cluster: {self.global_cluster_id}...")
        try:
            resp = self.rds.describe_global_clusters(GlobalClusterIdentifier=self.global_cluster_id)
            cluster = resp["GlobalClusters"][0]
            
            members = []
            for m in cluster["GlobalClusterMembers"]:
                members.append({
                    "cluster_arn": m["DBClusterArn"],
                    "is_writer": m["IsWriter"],
                    "readers": m.get("Readers", [])
                })
            
            return {
                "status": cluster["Status"],
                "engine": cluster["Engine"],
                "storage_encrypted": cluster["StorageEncrypted"],
                "members": members,
                "failover_ready": len(members) >= 2
            }
        except Exception as err:
            return {"error": str(err)}

    def audit_dynamodb_global_table(self) -> dict:
        """Inspects DynamoDB Global Table replica health across all regions."""
        logger.info(f"Auditing DynamoDB Global Table: {self.ddb_table_name}...")
        try:
            resp = self.ddb.describe_table(TableName=self.ddb_table_name)
            replicas = resp["Table"].get("Replicas", [])
            
            replica_status = []
            for r in replicas:
                replica_status.append({
                    "region": r["RegionName"],
                    "status": r["ReplicaStatus"],
                    "provisioned_throughput_override": "Custom" if "ProvisionedThroughputOverride" in r else "Inherited"
                })
                
            return {
                "table_name": self.ddb_table_name,
                "item_count": resp["Table"]["ItemCount"],
                "table_status": resp["Table"]["TableStatus"],
                "replicas": replica_status
            }
        except Exception as err:
            return {"error": str(err)}

if __name__ == "__main__":
    monitor = GlobalDatabaseMonitor(
        global_cluster_id="enterprise-core-global-db",
        ddb_table_name="GlobalCustomerLedger"
    )
    aurora_report = monitor.audit_aurora_global_cluster()
    ddb_report = monitor.audit_dynamodb_global_table()

    print("\n" + "="*50)
    print("ENTERPRISE DATABASE SOVEREIGNTY AUDIT REPORT")
    print("="*50)
    print("Aurora Global Database Status:")
    print(json.dumps(aurora_report, indent=2))
    print("\nDynamoDB Global Tables Status:")
    print(json.dumps(ddb_report, indent=2))
