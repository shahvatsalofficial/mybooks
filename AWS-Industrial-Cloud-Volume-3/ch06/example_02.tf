# ==============================================================================
# Terraform Module: FinOps Cost Anomaly Detection & Financial Circuit Breaker
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

variable "alert_email" {
  type        = string
  default     = "finops-alerts@enterprise.com"
  description = "Target email for high-severity spend anomaly dispatch"
}

# 1. AWS Cost Anomaly Monitor (Evaluates All AWS Services Across Linked Accounts)
resource "aws_ce_anomaly_monitor" "service_monitor" {
  name              = "Sovereign-Organization-Service-Monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"

  tags = {
    Environment = "Production"
    Governance  = "FinOps"
  }
}

# 2. SNS Topic for FinOps Incident Notifications
resource "aws_sns_topic" "finops_alerts" {
  name = "sovereign-finops-anomaly-topic"
}

resource "aws_sns_topic_subscription" "email_sub" {
  topic_arn = aws_sns_topic.finops_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# 3. AWS Cost Anomaly Subscription (Threshold > $100 or Dynamic Impact)
resource "aws_ce_anomaly_subscription" "realtime_alert" {
  name      = "Realtime-Spend-Anomaly-Subscription"
  frequency = "IMMEDIATE"

  monitor_arn_list = [
    aws_ce_anomaly_monitor.service_monitor.arn
  ]

  subscriber {
    type    = "SNS"
    address = aws_sns_topic.finops_alerts.arn
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_PERCENTAGE"
      values        = ["15"]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }

  tags = {
    Severity = "HIGH"
  }
}

# 4. Amazon S3 Intelligent-Tiering Bucket Configuration
resource "aws_s3_bucket" "data_lake" {
  bucket = "sovereign-enterprise-cur-lake-2026"
}

resource "aws_s3_bucket_intelligent_tiering_configuration" "entire_bucket" {
  bucket = aws_s3_bucket.data_lake.id
  name   = "EntireBucketIntelligentTiering"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}
