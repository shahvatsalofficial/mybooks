# Create EKS Pod Identity Association using AWS CLI
aws eks create-pod-identity-association   --cluster-name industrial-eks-prod   --namespace payment-tier   --service-account payment-processor-sa   --role-arn arn:aws:iam::112233445566:role/PaymentDynamoDbAccessRole
