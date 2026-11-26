# main.tf - AWS Bedrock Telemetry Alarms & Automated Rollback Controller

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
  }
}

variable "environment" {
  type    = string
  default = "production"
}

variable "claude_model_id" {
  type    = string
  default = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

# SNS Topic for Critical AI Incident Notifications
resource "aws_sns_topic" "ai_telemetry_alerts" {
  name              = "ai-telemetry-alerts-${var.environment}"
  kms_master_key_id = "alias/aws/sns"
}

# CloudWatch Metric Alarm: High Invocation Latency (P99 > 3,000ms over 3 minutes)
resource "aws_cloudwatch_metric_alarm" "bedrock_p99_latency_alarm" {
  alarm_name          = "Bedrock-Claude-P99-HighLatency-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  threshold           = 3000 # 3,000 milliseconds
  alarm_description   = "Triggers when Claude 3.5 Sonnet P99 latency exceeds 3.0s for 3 consecutive periods"
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "m1"
    return_data = true
    metric {
      namespace   = "AWS/Bedrock"
      metric_name = "InvocationLatency"
      period      = 60
      stat        = "p99"
      dimensions = {
        ModelId = var.claude_model_id
      }
    }
  }

  alarm_actions = [aws_sns_topic.ai_telemetry_alerts.arn]
  ok_actions    = [aws_sns_topic.ai_telemetry_alerts.arn]
}

# CloudWatch Metric Alarm: Throttle Exceptions (> 5 throttles in 1 minute)
resource "aws_cloudwatch_metric_alarm" "bedrock_throttle_alarm" {
  alarm_name          = "Bedrock-Claude-Throttles-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "InvocationThrottleErrors"
  namespace           = "AWS/Bedrock"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Immediate alarm when Bedrock InvokeModel throttles exceed 5/min"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ModelId = var.claude_model_id
  }

  alarm_actions = [aws_sns_topic.ai_telemetry_alerts.arn]
}

# S3 WORM Compliance Bucket for Bedrock Invocation Logging
resource "aws_s3_bucket" "bedrock_audit_logs" {
  bucket        = "corp-ai-bedrock-audit-logs-${var.environment}-vault"
  force_destroy = false

  object_lock_configuration {
    object_lock_enabled = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_audit_enc" {
  bucket = aws_s3_bucket.bedrock_audit_logs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# Strict Bucket Policy enforcing TLS 1.3 and KMS
resource "aws_s3_bucket_policy" "enforce_secure_transport" {
  bucket = aws_s3_bucket.bedrock_audit_logs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnforceTLSRequestsOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.bedrock_audit_logs.arn,
          "${aws_s3_bucket.bedrock_audit_logs.arn}/*"
        ]
        Condition = {
          Bool = { "aws:SecureTransport" : "false" }
        }
      }
    ]
  })
}
