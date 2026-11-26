#!/usr/bin/env python3
"""
Multi-Account SCP Compliance & Root Key Audit Engine
AWS Industrial Cloud Series — Volume 3
Author: Vatsal Shah (Enterprise Security & AI Architect)
"""

import boto3
import json
import logging
from typing import Dict, List, Set, Any
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s'
)
logger = logging.getLogger(__name__)

MANDATORY_ROOT_SCPS: Set[str] = {
    "DenyUnapprovedRegions",
    "ProtectSecurityServicesAndLogging",
    "PreventLeavingOrganization"
}

MANDATORY_WORKLOAD_SCPS: Set[str] = {
    "EnforceS3BlockPublicAccess",
    "DenyKMSKeyDeletion"
}

class OrganizationComplianceAuditor:
    def __init__(self):
        self.org_client = boto3.client('organizations')
        self.sts_client = boto3.client('sts')
        self.non_compliant_entities: List[Dict[str, Any]] = []

    def get_root_id(self) -> str:
        """Retrieve the Organizations Root ID."""
        try:
            response = self.org_client.list_roots()
            roots = response.get('Roots', [])
            if not roots:
                raise RuntimeError("No AWS Organizations roots found.")
            root_id = roots[0]['Id']
            logger.info(f"Identified Organizations Root ID: {root_id}")
            return root_id
        except ClientError as err:
            logger.error(f"Failed to retrieve Organization root: {err}")
            raise

    def get_attached_scps(self, target_id: str) -> Set[str]:
        """Fetch names of all Service Control Policies attached to a target."""
        attached_scps: Set[str] = set()
        paginator = self.org_client.get_paginator('list_policies_for_target')
        try:
            for page in paginator.paginate(TargetId=target_id, Filter='SERVICE_CONTROL_POLICY'):
                for policy in page.get('Policies', []):
                    attached_scps.add(policy['Name'])
            return attached_scps
        except ClientError as err:
            logger.error(f"Error fetching SCPs for target {target_id}: {err}")
            return attached_scps

    def audit_ou_recursive(self, parent_id: str, parent_path: str = "Root"):
        """Recursively traverse OUs and validate policy compliance."""
        logger.info(f"Auditing OU Path: {parent_path} (ID: {parent_id})")
        attached_scps = self.get_attached_scps(parent_id)

        # Validate Root / Core OU policies
        if parent_id.startswith('r-'):
            missing_scps = MANDATORY_ROOT_SCPS - attached_scps
            if missing_scps:
                self.non_compliant_entities.append({
                    "EntityId": parent_id,
                    "Path": parent_path,
                    "Type": "ROOT",
                    "MissingSCPs": list(missing_scps)
                })

        # Process Child OUs
        ou_paginator = self.org_client.get_paginator('list_organizational_units_for_parent')
        for page in ou_paginator.paginate(ParentId=parent_id):
            for ou in page.get('OrganizationalUnits', []):
                ou_id = ou['Id']
                ou_name = ou['Name']
                current_path = f"{parent_path} / {ou_name}"
                ou_scps = self.get_attached_scps(ou_id)

                if "Workloads" in ou_name:
                    missing_workload = MANDATORY_WORKLOAD_SCPS - (attached_scps | ou_scps)
                    if missing_workload:
                        self.non_compliant_entities.append({
                            "EntityId": ou_id,
                            "Path": current_path,
                            "Type": "OU",
                            "MissingSCPs": list(missing_workload)
                        })

                # Recursively audit nested OUs
                self.audit_ou_recursive(ou_id, current_path)

        # Process Member Accounts in this OU
        acc_paginator = self.org_client.get_paginator('list_accounts_for_parent')
        for page in acc_paginator.paginate(ParentId=parent_id):
            for acc in page.get('Accounts', []):
                acc_id = acc['Id']
                acc_name = acc['Name']
                self.audit_member_account_security(acc_id, f"{parent_path} / {acc_name}")

    def audit_member_account_security(self, account_id: str, account_path: str):
        """Assume cross-account role and verify root credentials and baseline security."""
        role_arn = f"arn:aws:iam::{account_id}:role/AWSControlTowerExecution"
        try:
            assumed = self.sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName="ContinuousSecurityAuditSession",
                DurationSeconds=900
            )
            creds = assumed['Credentials']
            iam_client = boto3.client(
                'iam',
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretAccessKey'],
                aws_session_token=creds['SessionToken']
            )

            # Audit Root Account Access Keys
            summary = iam_client.get_account_summary().get('SummaryMap', {})
            root_keys = summary.get('AccountAccessKeysPresent', 0)
            root_mfa = summary.get('AccountMFAEnabled', 0)

            if root_keys > 0:
                logger.critical(f"CRITICAL: Account {account_id} ({account_path}) has ACTIVE ROOT ACCESS KEYS!")
                self.non_compliant_entities.append({
                    "EntityId": account_id,
                    "Path": account_path,
                    "Type": "ACCOUNT_CRITICAL",
                    "Issue": "Active Root Access Keys Found! (Immediate Deletion Required)"
                })

            if root_mfa == 0 and not account_path.startswith("Root / Suspended"):
                self.non_compliant_entities.append({
                    "EntityId": account_id,
                    "Path": account_path,
                    "Type": "ACCOUNT_WARNING",
                    "Issue": "Root MFA is Not Enabled"
                })

        except ClientError as err:
            logger.warning(f"Could not assume role into account {account_id}: {err}")

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Run full audit and return structured telemetry report."""
        root_id = self.get_root_id()
        self.audit_ou_recursive(root_id)
        
        report = {
            "TotalViolations": len(self.non_compliant_entities),
            "Status": "FAILED" if self.non_compliant_entities else "COMPLIANT",
            "Violations": self.non_compliant_entities
        }
        logger.info(f"Audit Complete. Status: {report['Status']} ({report['TotalViolations']} findings)")
        return report

if __name__ == "__main__":
    auditor = OrganizationComplianceAuditor()
    compliance_report = auditor.generate_compliance_report()
    print(json.dumps(compliance_report, indent=2))
