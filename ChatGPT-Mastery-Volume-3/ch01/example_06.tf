# main.tf — Enterprise Azure OpenAI Zero-Trust Enclave Module
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90.0"
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

variable "prefix" {
  type        = string
  default     = "aoai-prod"
  description = "Standard enterprise resource prefix"
}

variable "location" {
  type        = string
  default     = "eastus2"
  description = "Primary deployment Azure region"
}

resource "azurerm_resource_group" "rg" {
  name     = "${var.prefix}-rg"
  location = var.location
  tags = {
    Environment = "Production"
    ManagedBy   = "Terraform"
    CostCenter  = "CC-4019"
  }
}

# Hub-and-Spoke Virtual Network Architecture
resource "azurerm_virtual_network" "vnet" {
  name                = "${var.prefix}-vnet"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  address_space       = ["10.200.0.0/16"]
}

resource "azurerm_subnet" "endpoint_subnet" {
  name                 = "snet-private-endpoints"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.200.4.0/24"]

  enforce_private_link_endpoint_network_policies = true
}

# User-Assigned Managed Identity for Key Vault CMK Access
resource "azurerm_user_assigned_identity" "aoai_identity" {
  name                = "${var.prefix}-identity"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
}

# Azure Key Vault HSM with Purge Protection
resource "azurerm_key_vault" "kv" {
  name                        = "${var.prefix}-kv-hsm"
  location                    = azurerm_resource_group.rg.location
  resource_group_name         = azurerm_resource_group.rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "premium"
  soft_delete_retention_days  = 90
  purge_protection_enabled    = true
  enable_rbac_authorization   = true

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
    virtual_network_subnet_ids = [azurerm_subnet.endpoint_subnet.id]
  }
}

# Primary Customer-Managed RSA Key
resource "azurerm_key_vault_key" "cmk" {
  name         = "aoai-root-kek"
  key_vault_id = azurerm_key_vault.kv.id
  key_type     = "RSA-HSM"
  key_size     = 4096

  key_opts = [
    "decrypt",
    "encrypt",
    "sign",
    "unwrapKey",
    "verify",
    "wrapKey"
  ]
}

# Azure OpenAI Cognitive Account with CMK and Zero Public Ingress
resource "azurerm_cognitive_account" "openai" {
  name                  = "${var.prefix}-account"
  location              = azurerm_resource_group.rg.location
  resource_group_name   = azurerm_resource_group.rg.name
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "${var.prefix}-enclave"

  public_network_access_enabled = false
  outbound_network_access_restricted = true

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aoai_identity.id]
  }

  customer_managed_key {
    key_vault_key_id   = azurerm_key_vault_key.cmk.id
    identity_client_id = azurerm_user_assigned_identity.aoai_identity.client_id
  }
}

# Private Endpoint Binding to Internal Subnet
resource "azurerm_private_endpoint" "pe" {
  name                = "${var.prefix}-pe"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  subnet_id           = azurerm_subnet.endpoint_subnet.id

  private_service_connection {
    name                           = "psc-aoai-core"
    private_connection_resource_id = azurerm_cognitive_account.openai.id
    is_manual_connection           = false
    subresource_names              = ["account"]
  }

  private_dns_zone_group {
    name                 = "pdz-group-openai"
    private_dns_zone_ids = [azurerm_private_dns_zone.dns_zone.id]
  }
}

# Private DNS Zone Linked to Corporate VNet
resource "azurerm_private_dns_zone" "dns_zone" {
  name                = "privatelink.openai.azure.com"
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "vnet_link" {
  name                  = "vnet-link-primary"
  resource_group_name   = azurerm_resource_group.rg.name
  private_dns_zone_name = azurerm_private_dns_zone.dns_zone.name
  virtual_network_id    = azurerm_virtual_network.vnet.id
}

data "azurerm_client_config" "current" {}
