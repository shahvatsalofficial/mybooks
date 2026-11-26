import boto3

def emergency_key_restoration(key_arn: str):
    kms = boto3.client('kms')
    
    # 1. Cancel the pending deletion window
    logger.info(f"Cancelling deletion for KMS Key: {key_arn}")
    kms.cancel_key_deletion(KeyId=key_arn)
    
    # 2. Re-enable the key for active cryptography
    logger.info(f"Re-enabling cryptographic state for: {key_arn}")
    kms.enable_key(KeyId=key_arn)
    
    # 3. Verify key state
    metadata = kms.describe_key(KeyId=key_arn)['KeyMetadata']
    assert metadata['KeyState'] == 'Enabled', "Key must be in Enabled state!"
    logger.info("KMS Key successfully restored to ENABLED state.")

emergency_key_restoration("arn:aws:kms:us-east-1:111122223333:key/cmk-finance-ledger")
