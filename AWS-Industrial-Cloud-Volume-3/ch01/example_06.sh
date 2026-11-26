# 1. Register Delegated Administrator for Security Hub
aws organizations register-delegated-administrator \
    --account-id 111122223333 \
    --service-principal securityhub.amazonaws.com

# 2. Enable Security Hub organization-wide with automatic member enrollment
aws securityhub enable-organization-admin-account \
    --admin-account-id 111122223333

# 3. Register Delegated Administrator for Amazon GuardDuty
aws organizations register-delegated-administrator \
    --account-id 111122223333 \
    --service-principal guardduty.amazonaws.com

# 4. Enable GuardDuty organization-wide with S3 and EKS runtime protection
aws guardduty enable-organization-admin-account \
    --admin-account-id 111122223333
