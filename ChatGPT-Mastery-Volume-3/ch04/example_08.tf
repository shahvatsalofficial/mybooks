# ingress_tier.tf — Application Gateway WAF v2 + APIM Backend
resource "azurerm_public_ip" "appgw_pip" {
  name                = "pip-appgw-ai-prod"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_subnet" "appgw_subnet" {
  name                 = "snet-appgw"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.200.0.0/24"]
}

resource "azurerm_web_application_firewall_policy" "waf_policy" {
  name                = "waf-policy-ai-edge"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  policy_settings {
    enabled                     = true
    mode                        = "Prevention"
    request_body_check          = true
    max_request_body_size_in_kb = 128
    file_upload_limit_in_mb     = 100
  }

  managed_rules {
    managed_rule_set {
      type    = "OWASP"
      version = "3.2"
      rule_group_override {
        rule_group_name = "REQUEST-942-APPLICATION-ATTACK-SQLI"
        disabled_rules  = []
      }
    }
  }

  custom_rules {
    name      = "BlockPromptOverride"
    priority  = 10
    rule_type = "MatchRule"
    action    = "Block"

    match_conditions {
      match_variables {
        variable_name = "RequestBody"
      }
      operator           = "Regex"
      negation_condition = false
      match_values       = ["(?i)ignore\s+all\s+previous\s+instructions"]
    }
  }
}

resource "azurerm_application_gateway" "appgw" {
  name                = "appgw-ai-edge"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  firewall_policy_id  = azurerm_web_application_firewall_policy.waf_policy.id

  sku {
    name     = "WAF_v2"
    tier     = "WAF_v2"
    capacity = 3
  }

  gateway_ip_configuration {
    name      = "appgw-ip-config"
    subnet_id = azurerm_subnet.appgw_subnet.id
  }

  frontend_port {
    name = "port_443"
    port = 443
  }

  frontend_ip_configuration {
    name                 = "appgw-frontend-ip"
    public_ip_address_id = azurerm_public_ip.appgw_pip.id
  }

  backend_address_pool {
    name  = "apim-internal-pool"
    ip_addresses = ["10.200.2.10"] # Private IP of Internal APIM
  }

  backend_http_settings {
    name                  = "apim-https-settings"
    cookie_based_affinity = "Disabled"
    port                  = 443
    protocol              = "Https"
    request_timeout       = 120
    probe_name            = "apim-health-probe"
  }

  http_listener {
    name                           = "https-listener"
    frontend_ip_configuration_name = "appgw-frontend-ip"
    frontend_port_name             = "port_443"
    protocol                       = "Https"
    ssl_certificate_name           = "corp-wildcard-cert"
  }

  request_routing_rule {
    name                       = "rule-https-to-apim"
    rule_type                  = "Basic"
    http_listener_name         = "https-listener"
    backend_address_pool_name  = "apim-internal-pool"
    backend_http_settings_name = "apim-https-settings"
    priority                   = 100
  }

  probe {
    name                = "apim-health-probe"
    protocol            = "Https"
    path                = "/status-0123456789abcdef"
    host                = "apim.internal.corp"
    interval            = 10
    timeout             = 5
    unhealthy_threshold = 3
  }
}
