#!/usr/bin/env python3
"""
AWS Config Conformance Pack & Automated Compliance Evaluator
AWS Industrial Cloud Series — Volume 3
Author: Vatsal Shah (Enterprise Security & AI Architect)
"""

import boto3
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class SovereignComplianceEngine:
    def __init__(self, region_name: str = "us-east-1"):
        self.config_client = boto3.client('config', region_name=region_name)
        self.ssm_client = boto3.client('ssm', region_name=region_name)
        self.region = region_name

    def audit_config_rule_compliance(self, rule_name: str) -> List[Dict[str, Any]]:
        """
        Audits evaluation results for a specific AWS Config rule across resources.
        """
        logger.info(f"Auditing compliance for Config Rule [{rule_name}] in {self.region}...")
        results = []
        paginator = self.config_client.get_paginator('get_compliance_details_by_config_rule')
        
        for page in paginator.paginate(ConfigRuleName=rule_name):
            for result in page.get('EvaluationResults', []):
                qualifier = result.get('EvaluationResultIdentifier', {}).get('EvaluationResultQualifier', {})
                resource_type = qualifier.get('ResourceType')
                resource_id = qualifier.get('ResourceId')
                compliance = result.get('ComplianceType')
                
                results.append({
                    "ResourceType": resource_type,
                    "ResourceId": resource_id,
                    "Compliance": compliance,
                    "RecordedTime": str(result.get('ResultRecordedTime'))
                })
                
                if compliance == 'NON_COMPLIANT':
                    logger.warning(f"NON-COMPLIANT RESOURCE DETECTED: [{resource_type}] {resource_id}")
        
        return results

if __name__ == "__main__":
    engine = SovereignComplianceEngine()
    print("Sovereign Compliance Engine initialized.")
