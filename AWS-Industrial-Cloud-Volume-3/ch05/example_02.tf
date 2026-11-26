# ==============================================================================
# Terraform Module: Bedrock Generative AI, Knowledge Base & Guardrails
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

variable "collection_name" {
  type        = string
  default     = "sovereign-financial-vectors"
  description = "Name of OpenSearch Serverless vector collection"
}

# 1. OpenSearch Serverless Encryption Security Policy
resource "aws_opensearchserverless_security_policy" "encryption" {
  name        = "sovereign-encryption-policy"
  type        = "encryption"
  description = "Encryption policy using AWS-managed KMS key for vector collection"

  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource     = ["collection/${var.collection_name}"]
      }
    ]
    AWSOwnedKey = true
  })
}

# 2. OpenSearch Serverless Network Security Policy (Private VPC Access)
resource "aws_opensearchserverless_security_policy" "network" {
  name        = "sovereign-network-policy"
  type        = "network"
  description = "Network policy restricting access to internal VPC endpoints"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/${var.collection_name}"]
        },
        {
          ResourceType = "dashboard"
          Resource     = ["collection/${var.collection_name}"]
        }
      ]
      AllowFromPublic = false
    }
  ])
}

# 3. OpenSearch Serverless Vector Collection
resource "aws_opensearchserverless_collection" "vectors" {
  name       = var.collection_name
  type       = "VECTORSEARCH"
  depends_on = [aws_opensearchserverless_security_policy.encryption]

  tags = {
    Environment = "Production"
    Purpose     = "Bedrock-Knowledge-Base-Embeddings"
  }
}

# 4. Guardrails for Amazon Bedrock (Multi-Tier Safety Shield)
resource "aws_bedrock_guardrail" "enterprise_safety" {
  name                      = "sovereign-enterprise-guardrail"
  description               = "Zero-trust prompt injection defense, PII redaction and denied topics"
  blocked_input_messaging   = "Request blocked by enterprise security guardrails."
  blocked_outputs_messaging = "Response blocked by enterprise safety policies."

  content_policy_config {
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
    filters_config {
      type            = "MISCONDUCT"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
  }

  sensitive_information_policy_config {
    pii_entities_config {
      type   = "US_SOCIAL_SECURITY_NUMBER"
      action = "MASK"
    }
    pii_entities_config {
      type   = "CREDIT_DEBIT_CARD_NUMBER"
      action = "MASK"
    }
    pii_entities_config {
      type   = "AWS_ACCESS_KEY"
      action = "BLOCK"
    }
  }

  tags = {
    Compliance  = "SOC2-HIPAA"
    Environment = "Production"
  }
}
