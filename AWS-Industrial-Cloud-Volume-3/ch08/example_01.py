#!/usr/bin/env python3
"""
Master Specialty Architecture Validator & Compliance Evaluator
AWS Industrial Cloud Series — Volume 3
Author: Vatsal Shah (Enterprise Security & AI Architect)
"""

import boto3
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class MasterSpecialtyValidator:
    def __init__(self, region_name: str = "us-east-1"):
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.ec2_client = boto3.client('ec2', region_name=region_name)
        self.kms_client = boto3.client('kms', region_name=region_name)
        self.region = region_name

    def validate_tgw_appliance_mode(self) -> List[Dict[str, Any]]:
        """
        Validates that all Transit Gateway attachments to Inspection VPCs have Appliance Mode ENABLED.
        """
        logger.info("Validating Transit Gateway Appliance Mode configurations...")
        results = []
        try:
            response = self.ec2_client.describe_transit_gateway_vpc_attachments()
            for attach in response.get('TransitGatewayVpcAttachments', []):
                attach_id = attach.get('TransitGatewayAttachmentId')
                vpc_id = attach.get('VpcId')
                appliance_mode = attach.get('Options', {}).get('ApplianceModeSupport', 'disable')
                
                status = "COMPLIANT" if appliance_mode == 'enable' else "NON_COMPLIANT"
                results.append({
                    "AttachmentId": attach_id,
                    "VpcId": vpc_id,
                    "ApplianceMode": appliance_mode,
                    "Status": status
                })
                logger.info(f"TGW Attachment [{attach_id}] on VPC [{vpc_id}]: ApplianceMode={appliance_mode} -> {status}")
        except Exception as e:
            logger.error(f"Error describing TGW attachments: {e}")
        return results

    def validate_s3_block_public_access(self, bucket_name: str) -> Dict[str, Any]:
        """
        Validates that all 4 S3 Block Public Access settings are strictly enabled.
        """
        logger.info(f"Validating S3 Block Public Access on bucket [{bucket_name}]...")
        try:
            response = self.s3_client.get_public_access_block(Bucket=bucket_name)
            pab = response.get('PublicAccessBlockConfiguration', {})
            
            all_blocked = (
                pab.get('BlockPublicAcls', False) and
                pab.get('IgnorePublicAcls', False) and
                pab.get('BlockPublicPolicy', False) and
                pab.get('RestrictPublicBuckets', False)
            )
            
            return {
                "Bucket": bucket_name,
                "AllBlocked": all_blocked,
                "Status": "COMPLIANT" if all_blocked else "NON_COMPLIANT",
                "Details": pab
            }
        except Exception as e:
            logger.error(f"Failed to get Public Access Block for {bucket_name}: {e}")
            return {"Bucket": bucket_name, "Status": "ERROR", "Error": str(e)}

if __name__ == "__main__":
    validator = MasterSpecialtyValidator()
    print("=== Master Specialty Architecture Evaluation ===")
    tgw_results = validator.validate_tgw_appliance_mode()
    print(json.dumps({"TGW_Appliance_Mode_Audit": tgw_results}, indent=2))
