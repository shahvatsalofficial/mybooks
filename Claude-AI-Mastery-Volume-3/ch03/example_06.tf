# Recipe 03.2: Terraform HCL Module for Vertex AI Private Service Connect (PSC)
# Author: Vatsal Shah (Lead Enterprise AI Architect)
# Architecture: Claude AI Mastery Series — Volume 3

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.20.0"
    }
  }
}

variable "project_id" {
  type        = string
  description = "Target Google Cloud Project ID"
}

variable "region" {
  type        = string
  default     = "us-east5"
  description = "Regional deployment target for Vertex AI Claude"
}

variable "network_id" {
  type        = string
  description = "Self-link of the VPC Network"
}

variable "subnet_id" {
  type        = string
  description = "Self-link of the Subnet for PSC endpoints"
}

# 1. Reserve Internal IP Address for Vertex AI PSC Forwarding Rule
resource "google_compute_address" "vertex_psc_address" {
  name         = "vertex-ai-psc-ip-${var.region}"
  project      = var.project_id
  region       = var.region
  subnetwork   = var.subnet_id
  address_type = "INTERNAL"
  purpose      = "GCE_ENDPOINT"
  description  = "Dedicated RFC 1918 Private IP for Vertex AI Claude Ingestion"
}

# 2. Provision Private Service Connect (PSC) Global Forwarding Rule
resource "google_compute_forwarding_rule" "vertex_psc_forwarding_rule" {
  name                  = "vertex-ai-psc-rule-${var.region}"
  project               = var.project_id
  region                = var.region
  network               = var.network_id
  ip_address            = google_compute_address.vertex_psc_address.id
  load_balancing_scheme = ""
  target                = "https://www.googleapis.com/compute/v1/projects/${var.project_id}/regions/${var.region}/serviceAttachments/google-vertex-ai-${var.region}"

  labels = {
    workload    = "claude-ai-inference"
    environment = "production"
    architect   = "vatsal-shah"
  }
}

# 3. Private DNS Managed Zone for Vertex AI Hostname Resolution
resource "google_dns_managed_zone" "vertex_private_zone" {
  name        = "vertex-ai-private-zone"
  project     = var.project_id
  dns_name    = "aiplatform.googleapis.com."
  description = "Private DNS Zone routing Vertex AI Claude traffic to PSC"
  visibility  = "private"

  private_visibility_config {
    networks {
      network_url = var.network_id
    }
  }
}

# 4. Regional DNS Record Mapping regional host to PSC Private IP
resource "google_dns_record_set" "vertex_regional_record" {
  name         = "${var.region}-aiplatform.googleapis.com."
  project      = var.project_id
  managed_zone = google_dns_managed_zone.vertex_private_zone.name
  type         = "A"
  ttl          = 300
  rrdatas      = [google_compute_address.vertex_psc_address.address]
}

output "vertex_psc_ip" {
  value       = google_compute_address.vertex_psc_address.address
  description = "Allocated internal IP address for Vertex AI Claude inference"
}
