# ==============================================================================
# Recipe 01.2: Terraform Module for AWS Bedrock Interface VPC Endpoint
# Architecture: Claude AI Mastery Series — Volume 3
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.30.0"
    }
  }
}

variable "vpc_id" {
  type        = string
  description = "Target enterprise VPC identifier"
}

variable "subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs across 3 AZs for ENI placement"
}

variable "allowed_ingress_cidrs" {
  type        = list(string)
  description = "CIDR blocks permitted to invoke Bedrock via PrivateLink"
  default     = ["10.100.0.0/16"]
}

variable "aws_region" {
  type        = string
  description = "AWS operational region"
  default     = "us-east-1"
}

# ------------------------------------------------------------------------------
# 1. Security Group: Strict Port 443 Ingress Only
# ------------------------------------------------------------------------------
resource "aws_security_group" "bedrock_vpce_sg" {
  name        = "sg-enterprise-bedrock-vpce"
  description = "Controls TLS 1.3 ingress to Amazon Bedrock Interface VPC Endpoint"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow TLS 1.3 inbound from internal application subnets"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_ingress_cidrs
  }

  egress {
    description = "Disallow all outbound traffic from VPC Endpoint ENIs"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "bedrock-vpce-security-group"
    Environment = "Production"
    Compliance  = "PCI-DSS-HIPAA-ZeroTrust"
  }
}

# ------------------------------------------------------------------------------
# 2. Interface VPC Endpoint for Bedrock Runtime
# ------------------------------------------------------------------------------
resource "aws_vpc_endpoint" "bedrock_runtime" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.bedrock_vpce_sg.id]
  private_dns_enabled = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnforceTLSRequestsOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "bedrock:*"
        Resource  = "*"
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid       = "RestrictToApprovedClaudeModelsOnly"
        Effect    = "Allow"
        Principal = "*"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Converse",
          "bedrock:ConverseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-5-sonnet-*",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-5-haiku-*",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-7-sonnet-*",
          "arn:aws:bedrock:${var.aws_region}:*:inference-profile/us.anthropic.claude-*"
        ]
      }
    ]
  })

  tags = {
    Name        = "bedrock-runtime-vpce-private"
    Service     = "AmazonBedrockRuntime"
    Environment = "Production"
  }
}

output "endpoint_id" {
  value       = aws_vpc_endpoint.bedrock_runtime.id
  description = "The ID of the Interface VPC Endpoint"
}

output "dns_entries" {
  value       = aws_vpc_endpoint.bedrock_runtime.dns_entry
  description = "Private DNS entries for the Bedrock interface endpoint"
}
