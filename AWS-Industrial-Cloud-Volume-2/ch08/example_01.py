#!/usr/bin/env python3
"""
AWS Industrial Cloud Series — Volume 2
Production Tool: DOP-C02 Multi-Account DevOps Maturity & Security Auditor
Author: Vatsal Shah
"""

import boto3
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("DevOpsAuditor")

class DevOpsMaturityAuditor:
    def __init__(self, region_name: str = "us-east-1"):
        self.region = region_name
        self.s3 = boto3.client('s3', region_name=region_name)
        self.config = boto3.client('config', region_name=region_name)
        self.oam = boto3.client('oam', region_name=region_name)

    def audit_s3_object_locks(self) -> list:
        """Audits S3 state buckets for Object Lock compliance."""
        logger.info("Auditing S3 buckets for Object Lock compliance...")
        gaps = []
        buckets = self.s3.list_buckets().get('Buckets', [])
        for b in buckets:
            name = b['Name']
            if 'tfstate' in name or 'iac' in name:
                try:
                    lock = self.s3.get_object_lock_configuration(Bucket=name)
                    mode = lock.get('ObjectLockConfiguration', {}).get('Rule', {}).get('DefaultRetention', {}).get('Mode')
                    if mode != 'COMPLIANCE':
                        logger.warning(f"⚠️ S3 Bucket '{name}' lacks Compliance Object Lock (Current: {mode})")
                        gaps.append({"bucket": name, "gap": "MissingComplianceLock"})
                    else:
                        logger.info(f"✅ S3 Bucket '{name}': Object Lock COMPLIANCE verified")
                except ClientError:
                    logger.warning(f"⚠️ S3 Bucket '{name}' does NOT have Object Lock enabled!")
                    gaps.append({"bucket": name, "gap": "ObjectLockDisabled"})
        return gaps

    def audit_oam_links(self) -> list:
        """Verifies account is linked to centralized OAM sink."""
        logger.info("Auditing CloudWatch Observability Access Manager (OAM) links...")
        gaps = []
        try:
            links = self.oam.list_links().get('Items', [])
            if not links:
                logger.warning("⚠️ No CloudWatch OAM Links found in this account!")
                gaps.append({"resource": "AWS::OAM::Link", "gap": "NoCentralMonitoringLink"})
            else:
                logger.info(f"✅ Account is actively linked to central OAM Sink ({len(links)} links found)")
        except ClientError as err:
            logger.error(f"Error checking OAM: {err}")
        return gaps

if __name__ == "__main__":
    auditor = DevOpsMaturityAuditor()
    s3_gaps = auditor.audit_s3_object_locks()
    oam_gaps = auditor.audit_oam_links()
    logger.info(f"DOP-C02 Audit Complete. Identified {len(s3_gaps) + len(oam_gaps)} architectural gaps.")
