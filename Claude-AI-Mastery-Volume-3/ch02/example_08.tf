# Recipe 02.4: Terraform HCL Module for Bedrock Agent & Action Group
# Author: Vatsal Shah (Lead Enterprise AI Architect)
# Architecture: Claude AI Mastery Series — Volume 3

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40.0"
    }
  }
}

variable "project_name" {
  type        = string
  default     = "claude-trade-recon"
  description = "Project prefix for resource naming"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment target environment"
}

# 1. IAM Service Role for Amazon Bedrock Agent
resource "aws_iam_role" "bedrock_agent_role" {
  name = "${var.project_name}-agent-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowBedrockAssumeRole"
        Effect    = "Allow"
        Principal = { Service = "bedrock.amazonaws.com" }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
          ArnLike      = { "aws:SourceArn" = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*" }
        }
      }
    ]
  })
}

# 2. Bedrock Agent Foundation Model Invocation Policy
resource "aws_iam_role_policy" "bedrock_agent_model_policy" {
  name = "${var.project_name}-model-policy"
  role = aws_iam_role.bedrock_agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "AllowClaudeInvocation"
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
      },
      {
        Sid      = "AllowS3OpenAPISpecRead"
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.agent_assets.arn}/schemas/*"
      }
    ]
  })
}

# 3. Amazon Bedrock Agent Instance
resource "aws_bedrockagent_agent" "trade_agent" {
  agent_name                  = "${var.project_name}-agent"
  agent_resource_role_arn     = aws_iam_role.bedrock_agent_role.arn
  foundation_model            = "anthropic.claude-3-5-sonnet-20241022-v2:0"
  idle_session_ttl_in_seconds = 1800

  instruction = <<-EOT
    You are an autonomous Institutional Trade Reconciliation Agent.
    Your operational directive is to validate, inspect, and reconcile unsettled equity trades.
    Always execute /trades/{trade_id} using the trade_recon_group action group to retrieve real-time state.
    Never guess or extrapolate settlement amounts. If trade status is UNCONFIRMED, escalate to human clearing.
  EOT

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Architect   = "Vatsal Shah"
  }
}

# 4. Bedrock Action Group Registration
resource "aws_bedrockagent_agent_action_group" "recon_action_group" {
  action_group_name          = "trade_recon_group"
  agent_id                   = aws_bedrockagent_agent.trade_agent.id
  agent_version              = "DRAFT"
  action_group_state         = "ENABLED"
  description                = "Query institutional trade settlement ledgers and execute reconciliation audits."

  action_group_executor {
    lambda = aws_lambda_function.trade_handler.arn
  }

  api_schema {
    s3 {
      s3_bucket_name = aws_s3_bucket.agent_assets.id
      s3_object_key  = "schemas/trade_reconciliation_openapi.yaml"
    }
  }
}

# 5. Lambda Permission Granting Invocations from Bedrock Agent
resource "aws_lambda_permission" "allow_bedrock" {
  statement_id  = "AllowBedrockAgentInvocation"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trade_handler.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = aws_bedrockagent_agent.trade_agent.arn
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
