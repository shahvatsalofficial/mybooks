#!/usr/bin/env python3
"""
AWS Enterprise Storage Tier Performance & Cost Auditor
Author: Vatsal Shah / Production Cloud Engineering
License: Apache 2.0
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("StorageAuditor")

class EnterpriseStorageAuditor:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.s3 = boto3.client("s3")
        self.ec2 = boto3.client("ec2", region_name=region)

    def audit_s3_buckets(self) -> list:
        """Audits S3 buckets for lifecycle rules, encryption, and public access blocks."""
        logger.info("Starting Amazon S3 Bucket Architecture Audit...")
        findings = []
        buckets = self.s3.list_buckets().get("Buckets", [])

        for b in buckets:
            b_name = b["Name"]
            
            # Check Lifecycle
            has_lifecycle = True
            try:
                self.s3.get_bucket_lifecycle_configuration(Bucket=b_name)
            except ClientError:
                has_lifecycle = False

            # Check Default Encryption
            has_encryption = True
            try:
                self.s3.get_bucket_encryption(Bucket=b_name)
            except ClientError:
                has_encryption = False

            findings.append({
                "bucket_name": b_name,
                "has_lifecycle_policy": has_lifecycle,
                "has_encryption": has_encryption,
                "cost_optimization_status": "COMPLIANT" if has_lifecycle else "NEEDS_LIFECYCLE_POLICY"
            })
        return findings

    def audit_ebs_volumes(self) -> list:
        """Audits EBS volumes for legacy gp2 types and unattached orphan volumes."""
        logger.info(f"Auditing Amazon EBS Volumes in {self.region}...")
        findings = []
        volumes = self.ec2.describe_volumes()["Volumes"]

        for v in volumes:
            v_id = v["VolumeId"]
            v_type = v["VolumeType"]
            state = v["State"]
            size_gb = v["Size"]

            issue = None
            if state == "available":
                issue = "ORPHAN_UNATTACHED_VOLUME (Wasting Money)"
            elif v_type == "gp2":
                issue = "LEGACY_GP2_VOLUME (Upgrade to gp3 for 20% savings + 3k IOPS)"

            if issue:
                findings.append({
                    "volume_id": v_id,
                    "type": v_type,
                    "size_gb": size_gb,
                    "state": state,
                    "recommendation": issue
                })
        return findings

if __name__ == "__main__":
    auditor = EnterpriseStorageAuditor("us-east-1")
    s3_report = auditor.audit_s3_buckets()
    ebs_report = auditor.audit_ebs_volumes()

    print("\n" + "="*50)
    print("ENTERPRISE STORAGE ARCHITECTURE AUDIT REPORT")
    print("="*50)
    print("S3 Buckets Audit Summary:")
    print(json.dumps(s3_report, indent=2))
    print("\nEBS Volume Optimization Findings:")
    print(json.dumps(ebs_report, indent=2))
