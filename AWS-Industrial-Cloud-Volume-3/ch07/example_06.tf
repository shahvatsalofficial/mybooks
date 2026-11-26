# ==============================================================================
# Terraform Module: AWS Config Organization Conformance Pack & Auto-Remediation
# AWS Industrial Cloud Series — Volume 3
# Author: Vatsal Shah (Enterprise Security & AI Architect)
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
  }
}

# 1. AWS Config Recorder & Delivery Channel
resource "aws_config_configuration_recorder" "org_recorder" {
  name     = "sovereign-org-config-recorder"
  role_arn = aws_iam_role.config_role.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_iam_role" "config_role" {
  name = "SovereignConfigRecorderRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })
}

# 2. Managed Config Rule: S3 Bucket SSE KMS Encryption Mandatory
resource "aws_config_config_rule" "s3_kms_encryption" {
  name        = "s3-bucket-server-side-encryption-enabled"
  description = "Ensures that all Amazon S3 buckets are encrypted with KMS CMK."

  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED"
  }

  scope {
    compliance_resource_types = ["AWS::S3::Bucket"]
  }

  depends_on = [aws_config_configuration_recorder.org_recorder]
}

# 3. Automated SSM Remediation Configuration
resource "aws_config_remediation_configuration" "s3_kms_remediation" {
  config_rule_name = aws_config_config_rule.s3_kms_encryption.name
  target_type      = "SSM_DOCUMENT"
  target_id        = "AWS-EnableS3BucketEncryption"
  target_version   = "1"

  parameter {
    name           = "BucketName"
    resource_value = "RESOURCE_ID"
  }

  parameter {
    name         = "SSEAlgorithm"
    static_value = "aws:kms"
  }

  parameter {
    name         = "AutomationAssumeRole"
    static_value = "arn:aws:iam::111122223333:role/AWSConfigRemediationRole"
  }

  automatic                  = true
  maximum_automatic_attempts = 3
  retry_attempt_seconds      = 10
}
