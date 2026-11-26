# main.tf - Hardened Azure OpenAI Infrastructure
resource "azurerm_cognitive_account" "openai_instance" {
  name                          = "oai-enterprise-prod-eastus"
  location                      = "eastus"
  resource_group_name           = var.resource_group_name
  kind                          = "OpenAI"
  sku_name                      = "S0"
  public_network_access_enabled = false
  custom_subdomain_name         = "corp-ai-eastus-prod"

  identity {
    type = "SystemAssigned, UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.ai_cmk_identity.id]
  }

  customer_managed_key {
    key_vault_key_id   = azurerm_key_vault_key.openai_cmk.id
    identity_client_id = azurerm_user_assigned_identity.ai_cmk_identity.client_id
  }

  network_acls {
    default_action = "Deny"
    ip_rules       = []
  }

  tags = {
    Environment = "Production"
    CostCenter  = "Enterprise-AI-Platform"
    Compliance  = "HIPAA-SOC2-EU-AI-Act"
  }
}

resource "azurerm_private_endpoint" "openai_private_endpoint" {
  name                = "pe-openai-prod"
  location            = "eastus"
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_subnet_id

  private_service_connection {
    name                           = "psc-openai-prod"
    private_connection_resource_id = azurerm_cognitive_account.openai_instance.id
    is_manual_connection           = false
    subresource_names              = ["account"]
  }

  private_dns_zone_group {
    name                 = "privatelink-openai-dns"
    private_dns_zone_ids = [var.private_dns_zone_id]
  }
}
