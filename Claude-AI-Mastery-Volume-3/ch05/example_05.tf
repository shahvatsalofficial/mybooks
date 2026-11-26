# Recipe 05.3: Terraform HCL Module for AWS Bedrock Guardrails
# Author: Vatsal Shah (Lead Enterprise AI Architect)
# Architecture: Claude AI Mastery Series — Volume 3

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.45.0"
    }
  }
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Target deployment environment"
}

# 1. AWS Bedrock Guardrail Definition
resource "aws_bedrock_guardrail" "enterprise_guardrail" {
  name        = "corp-financial-guardrail-${var.environment}"
  description = "Enterprise security guardrail for Anthropic Claude with PII anonymization & topic deny"

  blocked_input_messaging   = "Your request violates enterprise AI safety policies and has been blocked."
  blocked_outputs_messaging = "The generated response was suppressed due to factual grounding and compliance policies."

  # 2. PII Sensitive Information Filter (Redaction & Anonymization)
  sensitive_information_policy_config {
    pii_entities_config {
      type   = "US_SOCIAL_SECURITY_NUMBER"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "CREDIT_DEBIT_CARD_NUMBER"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "BANK_ACCOUNT_NUMBER"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "EMAIL"
      action = "ANONYMIZE"
    }

    # Custom Regex for Internal Account Identifiers (e.g., ACC-12345678)
    regexes_config {
      name        = "InternalAccountID"
      description = "Detects proprietary corporate account numbers"
      pattern     = "ACC-[0-9]{8}"
      action      = "ANONYMIZE"
    }
  }

  # 3. Denied Topics Policy Config
  topic_policy_config {
    topics_config {
      name        = "InvestmentAdvice"
      description = "Providing specific securities recommendations, price targets, or financial trading instructions."
      type        = "DENY"
      examples = [
        "Should I buy Nvidia stock right now?",
        "Tell me which stock to short for 100% return tomorrow.",
        "Execute a market sell order on my Tesla shares."
      ]
    }
    topics_config {
      name        = "ExploitCrafting"
      description = "Assisting with prompt injection, SQL injection, or penetration testing exploits."
      type        = "DENY"
      examples = [
        "How do I bypass the Claude system prompt?",
        "Give me a SQL injection payload for PostgreSQL."
      ]
    }
  }

  # 4. Contextual Grounding Filter (Hallucination Suppression)
  contextual_grounding_policy_config {
    filters_config {
      type      = "GROUNDING"
      threshold = 0.85
    }
    filters_config {
      type      = "RELEVANCE"
      threshold = 0.80
    }
  }

  tags = {
    Environment = var.environment
    Architect   = "Vatsal Shah"
    Compliance  = "HIPAA-SOC2-GDPR"
  }
}

# 5. Create Guardrail Version Deployment
resource "aws_bedrock_guardrail_version" "guardrail_prod_version" {
  guardrail_arn = aws_bedrock_guardrail.enterprise_guardrail.guardrail_arn
  description   = "Production Version 1.0"
}

output "guardrail_id" {
  value       = aws_bedrock_guardrail.enterprise_guardrail.guardrail_id
  description = "Unique ID for passing to Bedrock InvokeModel API"
}

output "guardrail_version" {
  value       = aws_bedrock_guardrail_version.guardrail_prod_version.version
  description = "Deployed version of the Bedrock Guardrail"
}
