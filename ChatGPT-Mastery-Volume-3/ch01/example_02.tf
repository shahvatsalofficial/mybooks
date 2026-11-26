# main.tf — Enterprise Zero-Trust Azure OpenAI Architecture

terraform {
  required_version = ">= 1.8.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
}

variable "location" {
  type    = string
  default = "eastus2"
}

variable "resource_group_name" {
  type    = string
  default = "rg-enterprise-ai-prod"
}

# 1. Resource Group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags = {
    Environment = "Production"
    CostCenter  = "Core-AI-Platform"
    Compliance  = "HIPAA-PCI-ISO27001"
  }
}

# 2. Virtual Network & Subnet
resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-ai-enclave"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.2.0.0/16"]
}

resource "azurerm_subnet" "pe_subnet" {
  name                 = "snet-private-endpoints"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.2.2.0/24"]
  
  # Crucial: Disable private endpoint network policies to allow NSGs
  private_endpoint_network_policies_enabled = true
}

# 3. User-Assigned Managed Identity for CMK
resource "azurerm_user_assigned_identity" "ai_identity" {
  name                = "id-aoai-crypto-service"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

# 4. Azure Key Vault with HSM and Purge Protection
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "kv" {
  name                        = "kv-ai-cmk-prod-01"
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "premium" # Required for HSM-backed keys
  soft_delete_retention_days  = 90
  purge_protection_enabled    = true

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_user_assigned_identity.ai_identity.principal_id

    key_permissions = [
      "Get", "UnwrapKey", "WrapKey"
    ]
  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Create", "Delete", "Get", "List", "Purge", "Recover", "Update"
    ]
  }
}

# 5. Key Encryption Key (KEK) 4096-bit RSA
resource "azurerm_key_vault_key" "cmk" {
  name         = "aoai-primary-kek"
  key_vault_id = azurerm_key_vault.kv.id
  key_type     = "RSA-HSM"
  key_size     = 4096

  key_opts = [
    "decrypt", "encrypt", "sign", "unwrapKey", "verify", "wrapKey"
  ]
}

# 6. Azure OpenAI Account with CMK and Disabled Public Access
resource "azurerm_cognitive_account" "aoai" {
  name                  = "aoai-enterprise-core-prod"
  location              = azurerm_resource_group.rg.location
  resource_group_name   = azurerm_resource_group.rg.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  
  # MANDATORY SECURITY GATES:
  public_network_access_enabled = false
  custom_subdomain_name         = "aoai-enterprise-core-prod"

  identity {
    type = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.ai_identity.id]
  }

  customer_managed_key {
    key_vault_key_id   = azurerm_key_vault_key.cmk.id
    identity_client_id = azurerm_user_assigned_identity.ai_identity.client_id
  }

  tags = {
    SecurityZone = "Enclave"
    ManagedBy    = "Terraform"
  }
}

# 7. Model Deployments (Explicit Version Pinning)
resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = "gpt-4o"
  cognitive_account_id = azurerm_cognitive_account.aoai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o"
    version = "2024-08-06" # STRICT PINNING
  }

  scale {
    type     = "Standard"
    capacity = 120 # Tokens Per Minute allocation (120k TPM)
  }
}

resource "azurerm_cognitive_deployment" "embeddings" {
  name                 = "text-embedding-3-large"
  cognitive_account_id = azurerm_cognitive_account.aoai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-large"
    version = "1"
  }

  scale {
    type     = "Standard"
    capacity = 50
  }
}

# 8. Private Endpoint
resource "azurerm_private_endpoint" "aoai_pe" {
  name                = "pe-aoai-core-prod"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  subnet_id           = azurerm_subnet.pe_subnet.id

  private_service_connection {
    name                           = "psc-aoai-prod"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_cognitive_account.aoai.id
    subresource_names              = ["account"]
  }
}

# 9. Private DNS Zone & Virtual Network Link
resource "azurerm_private_dns_zone" "dns_zone" {
  name                = "privatelink.openai.azure.com"
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "vnet_link" {
  name                  = "vnet-link-ai-dns"
  resource_group_name   = azurerm_resource_group.rg.name
  private_dns_zone_name = azurerm_private_dns_zone.dns_zone.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

resource "azurerm_private_dns_a_record" "dns_record" {
  name                = "aoai-enterprise-core-prod"
  zone_name           = azurerm_private_dns_zone.dns_zone.name
  resource_group_name = azurerm_resource_group.rg.name
  ttl                 = 300
  records             = [azurerm_private_endpoint.aoai_pe.private_service_connection[0].private_ip_address]
}
