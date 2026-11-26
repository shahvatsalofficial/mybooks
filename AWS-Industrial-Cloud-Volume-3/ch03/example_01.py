#!/usr/bin/env python3
"""
Autonomous Threat Containment Swarm Worker (15-Second SLA)
AWS Industrial Cloud Series — Volume 3
Author: Vatsal Shah (Enterprise Security & AI Architect)
"""

import boto3
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Step Functions Task Worker: Executes Multi-Account Threat Quarantine.
    """
    finding = event.get('detail', {})
    finding_id = finding.get('id')
    finding_type = finding.get('type')
    severity = finding.get('severity', 0.0)
    account_id = finding.get('accountId')
    resource = finding.get('resource', {})
    
    logger.info(f"Received High-Severity Finding [{finding_id}] ({finding_type}) in Account {account_id}")
    
    if severity < 7.0:
        logger.info(f"Finding severity {severity} < 7.0. Skipping automated quarantine.")
        return {"status": "SKIPPED", "reason": "Severity below threshold"}

    # 1. Assume cross-account SecOps execution role
    sts = boto3.client('sts')
    role_arn = f"arn:aws:iam::{account_id}:role/AWSControlTowerExecution"
    assumed = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName="AutomatedContainmentSwarmSession",
        DurationSeconds=900
    )
    creds = assumed['Credentials']
    
    ec2 = boto3.client(
        'ec2',
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken']
    )
    iam = boto3.client(
        'iam',
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken']
    )

    remediation_results = {}

    # 2. Check for EC2 Instance Compromise
    instance_details = resource.get('instanceDetails', {})
    instance_id = instance_details.get('instanceId')
    
    if instance_id:
        # A. Network Isolation via Quarantine Security Group
        vpcs = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['false']}])['Vpcs']
        vpc_id = instance_details.get('networkInterfaces', [{}])[0].get('vpcId')
        
        # Get or create quarantine security group
        sgs = ec2.describe_security_groups(
            Filters=[
                {'Name': 'group-name', 'Values': ['sg-quarantine-deny-all']},
                {'Name': 'vpc-id', 'Values': [vpc_id]}
            ]
        )['SecurityGroups']
        
        if sgs:
            quarantine_sg_id = sgs[0]['GroupId']
        else:
            quarantine_sg = ec2.create_security_group(
                GroupName='sg-quarantine-deny-all',
                Description='Automated Quarantine SG - Deny All Ingress and Egress',
                VpcId=vpc_id
            )
            quarantine_sg_id = quarantine_sg['GroupId']
            # Revoke default egress allow all
            ec2.revoke_security_group_egress(
                GroupId=quarantine_sg_id,
                IpPermissions=[{'IpProtocol': '-1', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]
            )

        # Apply Quarantine SG
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            Groups=[quarantine_sg_id]
        )
        remediation_results['NetworkIsolation'] = f"Attached {quarantine_sg_id}"
        logger.info(f"Successfully isolated instance {instance_id} into {quarantine_sg_id}")

        # B. Capture Forensic EBS Snapshots
        volumes = ec2.describe_volumes(
            Filters=[{'Name': 'attachment.instance-id', 'Values': [instance_id]}]
        )['Volumes']
        
        snapshot_ids = []
        for vol in volumes:
            vol_id = vol['VolumeId']
            snap = ec2.create_snapshot(
                VolumeId=vol_id,
                Description=f"Forensic Snapshot for Incident {finding_id} ({instance_id})",
                TagSpecifications=[{
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {'Key': 'IncidentID', 'Value': finding_id},
                        {'Key': 'ForensicEvidence', 'Value': 'True'},
                        {'Key': 'SourceInstance', 'Value': instance_id}
                    ]
                }]
            )
            snapshot_ids.append(snap['SnapshotId'])
        remediation_results['ForensicSnapshots'] = snapshot_ids
        logger.info(f"Initiated forensic snapshots: {snapshot_ids}")

    # 3. Check for Compromised IAM Role / User
    access_key_details = resource.get('accessKeyDetails', {})
    user_name = access_key_details.get('userName')
    role_name = access_key_details.get('roleName')
    
    if role_name:
        # Revoke all active sessions by enforcing TokenIssueTime policy
        now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        revocation_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": "*",
                    "Resource": "*",
                    "Condition": {
                        "DateLessThan": {
                            "aws:TokenIssueTime": now_iso
                        }
                    }
                }
            ]
        }
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="AutomatedSessionRevocationPolicy",
            PolicyDocument=json.dumps(revocation_policy)
        )
        remediation_results['IAMRevocation'] = f"Revoked active STS tokens for role {role_name} before {now_iso}"
        logger.info(f"Revoked STS sessions for role {role_name}")

    return {
        "status": "CONTAINED",
        "findingId": finding_id,
        "accountId": account_id,
        "remediation": remediation_results
    }
