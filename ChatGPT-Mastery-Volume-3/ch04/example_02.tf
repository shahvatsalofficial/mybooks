# main.tf - Zero-Trust Keyless Azure OpenAI Infrastructure
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "resource_group_name" {
  type    = string
  default = "rg-enterprise-ai-prod-eastus"
}

variable "location" {
  type    = string
  default = "eastus2"
}

# 1. User-Assigned Managed Identity for Application Fleet
resource "azurerm_user_assigned_identity" "app_workload_identity" {
  name                = "uami-ai-rag-worker-prod"
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = {
    Environment = "Production"
    ManagedBy   = "Terraform"
    SecurityTier = "Tier-0"
  }
}

# 2. Azure OpenAI Cognitive Account with Local Static Keys Disabled
resource "azurerm_cognitive_account" "aoai_service" {
  name                  = "aoai-core-enterprise-prod"
  location              = var.location
  resource_group_name   = var.resource_group_name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "aoai-core-enterprise-prod"

  # CRITICAL ZERO-TRUST DIRECTIVE: Disable all static API key authentication
  local_auth_enabled = false

  # Disable all public internet ingress
  public_network_access_enabled = false

  tags = {
    Environment = "Production"
    Compliance  = "PCI-DSS-HIPAA"
  }
}

# 3. Scoped Azure RBAC Assignment: Cognitive Services OpenAI User
# Role Definition ID: 5e6445fa-5234-45e0-9ad4-ed6e3bc091cd
resource "azurerm_role_assignment" "uami_openai_user" {
  scope                = azurerm_cognitive_account.aoai_service.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_user_assigned_identity.app_workload_identity.principal_id

  # Ensure role assignment does not delay during deployment
  skip_service_principal_aad_check = true
}

output "uami_client_id" {
  description = "Client ID to be injected into application pod environment variables"
  value       = azurerm_user_assigned_identity.app_workload_identity.client_id
}

output "aoai_endpoint" {
  description = "Private FQDN for the Azure OpenAI Service"
  value       = azurerm_cognitive_account.aoai_service.endpoint
}
