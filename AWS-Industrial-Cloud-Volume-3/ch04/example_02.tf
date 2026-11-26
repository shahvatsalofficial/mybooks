# ==============================================================================
# Terraform Module: Centralized Network Firewall Inspection Hub
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

variable "vpc_cidr" {
  type        = string
  default     = "10.250.0.0/16"
  description = "CIDR block for Centralized Inspection VPC"
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
  description = "Target Availability Zones for multi-AZ inspection"
}

variable "transit_gateway_id" {
  type        = string
  description = "ID of the core AWS Transit Gateway"
}

# 1. Dedicated Centralized Inspection VPC
resource "aws_vpc" "inspection" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "Sovereign-Central-Inspection-VPC"
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}

# 2. Firewall Subnets (One per AZ)
resource "aws_subnet" "firewall" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.inspection.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "Firewall-Subnet-${var.availability_zones[count.index]}"
  }
}

# 3. TGW Attachment Subnets (One per AZ)
resource "aws_subnet" "tgw_attachment" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.inspection.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "TGW-Attachment-Subnet-${var.availability_zones[count.index]}"
  }
}

# 4. AWS Transit Gateway VPC Attachment with Appliance Mode ENABLED
resource "aws_transit_gateway_vpc_attachment" "inspection" {
  transit_gateway_id                              = var.transit_gateway_id
  vpc_id                                          = aws_vpc.inspection.id
  subnet_ids                                      = aws_subnet.tgw_attachment[*].id
  appliance_mode_support                          = "enable"
  transit_gateway_default_route_table_association = false
  transit_gateway_default_route_table_propagation = false

  tags = {
    Name               = "TGW-Inspection-Attachment-ApplianceMode"
    ApplianceModeState = "Enabled"
  }
}

# 5. AWS Network Firewall Stateful Rule Group
resource "aws_networkfirewall_rule_group" "suricata_ips" {
  capacity = 1000
  name     = "sovereign-suricata-ips-rules"
  type     = "STATEFUL"

  rule_group {
    rules_source {
      rules_string = <<EOF
drop http $HOME_NET any -> $EXTERNAL_NET 80 (msg:"Block Cleartext HTTP Egress"; sid:1000001; rev:1;)
drop tls $HOME_NET any -> $EXTERNAL_NET 443 (msg:"Block Unauthorized Egress TLS"; tls_sni; content:!"amazonaws.com"; nocase; endswith; sid:1000002; rev:1;)
pass tcp 10.0.0.0/8 any -> 10.0.0.0/8 443 (msg:"Allow Internal Spoke HTTPS"; sid:1000003; rev:1;)
EOF
    }
    stateful_rule_options {
      rule_order = "STRICT_ORDER"
    }
  }

  tags = {
    Environment = "Production"
  }
}

# 6. AWS Network Firewall Policy & Firewall Instance
resource "aws_networkfirewall_firewall_policy" "policy" {
  name = "sovereign-inspection-policy"

  firewall_policy {
    stateless_default_actions          = ["aws:forward_to_sfe"]
    stateless_fragment_default_actions = ["aws:forward_to_sfe"]
    stateful_rule_group_reference {
      resource_arn = aws_networkfirewall_rule_group.suricata_ips.arn
    }
  }
}

resource "aws_networkfirewall_firewall" "cluster" {
  name                = "sovereign-network-firewall"
  firewall_policy_arn = aws_networkfirewall_firewall_policy.policy.arn
  vpc_id              = aws_vpc.inspection.id

  dynamic "subnet_mapping" {
    for_each = aws_subnet.firewall[*].id
    content {
      subnet_id = subnet_mapping.value
    }
  }

  tags = {
    Name = "Sovereign-Network-Firewall-Production"
  }
}
