import boto3
import os

def lambda_handler(event, context):
    finding = event['detail']
    account_id = finding['accountId']
    access_key_id = finding['service']['additionalInfo']['accessKeyId']
    
    # 1. Assume cross-account execution role
    sts = boto3.client('sts')
    role_arn = f"arn:aws:iam::{account_id}:role/AWSControlTowerExecution"
    assumed = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName="EmergencyContainmentSession"
    )
    
    creds = assumed['Credentials']
    iam = boto3.client(
        'iam',
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken']
    )
    
    # 2. Deactivate the compromised root access key immediately
    iam.update_access_key(
        UserName='root',
        AccessKeyId=access_key_id,
        Status='Inactive'
    )
    
    # 3. Permanently delete the access key
    iam.delete_access_key(
        UserName='root',
        AccessKeyId=access_key_id
    )
    
    # 4. Move account to Quarantine OU
    orgs = boto3.client('organizations')
    quarantine_ou_id = os.environ['QUARANTINE_OU_ID']
    
    # Find current parent
    parents = orgs.list_parents(ChildId=account_id)['Parents']
    current_parent_id = parents[0]['Id']
    
    orgs.move_account(
        AccountId=account_id,
        SourceParentId=current_parent_id,
        DestinationParentId=quarantine_ou_id
    )
    
    return {"status": "CONTAINED", "account": account_id, "key": access_key_id}
