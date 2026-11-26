#!/usr/bin/env python3
"""
AWS IAM Enterprise Privilege & Compliance Auditor
Author: Vatsal Shah / Security Architecture Lab
License: Apache 2.0
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IAM-Auditor")

class EnterpriseIamAuditor:
    def __init__(self):
        self.iam = boto3.client("iam")
        self.org = boto3.client("organizations")

    def audit_admin_roles(self):
        """Scans all IAM roles for overly permissive wildcard admin privileges."""
        logger.info("Starting IAM Role Privilege Audit...")
        dangerous_roles = []

        paginator = self.iam.get_paginator("list_roles")
        for page in paginator.paginate():
            for role in page["Roles"]:
                role_name = role["RoleName"]
                
                # Check attached managed policies
                attached_policies = self.iam.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
                for pol in attached_policies:
                    if pol["PolicyArn"] == "arn:aws:iam::aws:policy/AdministratorAccess":
                        has_boundary = "PermissionsBoundary" in role
                        dangerous_roles.append({
                            "role_name": role_name,
                            "policy": "AdministratorAccess",
                            "has_permissions_boundary": has_boundary,
                            "risk_level": "LOW" if has_boundary else "CRITICAL"
                        })
        return dangerous_roles

    def audit_scp_guardrails(self):
        """Verifies that mandatory security SCPs are attached to the Organization Root."""
        logger.info("Auditing Organizations Service Control Policies (SCPs)...")
        try:
            roots = self.org.list_roots()["Roots"]
            if not roots:
                return {"status": "NO_ORGANIZATION_FOUND"}

            root_id = roots[0]["Id"]
            attached_scps = self.org.list_policies_for_target(
                TargetId=root_id,
                Filter="SERVICE_CONTROL_POLICY"
            )["Policies"]

            scp_names = [scp["Name"] for scp in attached_scps]
            return {
                "root_id": root_id,
                "attached_scps": scp_names,
                "has_cloudtrail_protection": any("CloudTrail" in name for name in scp_names),
                "has_region_lock": any("Region" in name for name in scp_names)
            }
        except ClientError as err:
            return {"error": str(err)}

if __name__ == "__main__":
    auditor = EnterpriseIamAuditor()
    role_audit = auditor.audit_admin_roles()
    scp_audit = auditor.audit_scp_guardrails()
    
    print("\n" + "="*50)
    print("ENTERPRISE IAM SECURITY AUDIT REPORT")
    print("="*50)
    print("Overly Permissive / Unbounded Admin Roles:")
    print(json.dumps(role_audit, indent=2))
    print("\nOrganization Root SCP Compliance:")
    print(json.dumps(scp_audit, indent=2))
