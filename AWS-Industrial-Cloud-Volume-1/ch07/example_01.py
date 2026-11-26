#!/usr/bin/env python3
"""
AWS CloudFront & WAF Enterprise Security Auditor
Author: Vatsal Shah / Security Architecture Lab
License: Apache 2.0
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EdgeAuditor")

class EdgeSecurityAuditor:
    def __init__(self):
        self.cf = boto3.client("cloudfront")
        self.waf = boto3.client("wafv2", region_name="us-east-1") # CloudFront WAF is always us-east-1

    def audit_cloudfront_distributions(self) -> list:
        """Audits CloudFront distributions for OAC, HTTPS enforcement, and WAF attachment."""
        logger.info("Starting CloudFront Edge Distribution Audit...")
        findings = []
        
        paginator = self.cf.get_paginator("list_distributions")
        for page in paginator.paginate():
            items = page.get("DistributionList", {}).get("Items", [])
            for dist in items:
                dist_id = dist["Id"]
                domain = dist["DomainName"]
                waf_id = dist.get("WebACLId", "")
                
                # Check Default Cache Behavior Viewer Protocol Policy
                viewer_policy = dist["DefaultCacheBehavior"]["ViewerProtocolPolicy"]
                https_enforced = viewer_policy in ["redirect-to-https", "https-only"]
                
                # Check Origins for OAC vs OAI
                origins = dist["Origins"]["Items"]
                has_oac = any(o.get("OriginAccessControlId", "") != "" for o in origins)

                findings.append({
                    "distribution_id": dist_id,
                    "domain_name": domain,
                    "https_enforced": https_enforced,
                    "has_waf_attached": bool(waf_id),
                    "has_origin_access_control": has_oac,
                    "compliance_status": "COMPLIANT" if (https_enforced and waf_id and has_oac) else "NON_COMPLIANT"
                })
        return findings

    def audit_waf_web_acls(self) -> list:
        """Audits global CloudFront Web ACLs for rate-limiting and SQLi protections."""
        logger.info("Auditing AWS WAF Web ACL Rules...")
        findings = []
        
        web_acls = self.waf.list_web_acls(Scope="CLOUDFRONT")["WebACLs"]
        for acl in web_acls:
            detail = self.waf.get_web_acl(Name=acl["Name"], Scope="CLOUDFRONT", Id=acl["Id"])["WebACL"]
            rule_names = [r["Name"] for r in detail.get("Rules", [])]
            
            has_rate_limit = any("Rate" in name or "rate" in name for name in rule_names)
            has_sqli = any("SQLi" in name or "Common" in name for name in rule_names)
            
            findings.append({
                "web_acl_name": detail["Name"],
                "wcu_capacity": detail.get("Capacity", 0),
                "rules_count": len(rule_names),
                "has_rate_limiting": has_rate_limit,
                "has_sqli_protection": has_sqli
            })
        return findings

if __name__ == "__main__":
    auditor = EdgeSecurityAuditor()
    cf_report = auditor.audit_cloudfront_distributions()
    waf_report = auditor.audit_waf_web_acls()

    print("\n" + "="*50)
    print("ENTERPRISE EDGE DELIVERY & WAF AUDIT REPORT")
    print("="*50)
    print("CloudFront Distributions Compliance:")
    print(json.dumps(cf_report, indent=2))
    print("\nAWS WAF Web ACL Security Posture:")
    print(json.dumps(waf_report, indent=2))
