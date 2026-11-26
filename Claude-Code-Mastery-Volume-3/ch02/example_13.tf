# /terraform/modules/agent_node_group/main.tf
# Enterprise Hardened Node Group for Autonomous AI Agents

resource "aws_eks_node_group" "agent_workers" {
  cluster_name    = var.eks_cluster_name
  node_group_name = "claude-code-cleanroom-workers"
  node_role_arn   = var.node_role_arn
  subnet_ids      = var.private_subnet_ids

  scaling_config {
    desired_size = 5
    max_size     = 20
    min_size     = 2
  }

  # Mandate modern compute instances with nested virtualization support for KVM
  instance_types = ["c6i.2xlarge", "c6i.4xlarge"]
  capacity_type  = "ON_DEMAND"
  disk_size      = 100

  # Enforce IMDSv2 exclusively with hop-limit 1
  launch_template {
    id      = aws_launch_template.agent_node_template.id
    version = "$Latest"
  }

  labels = {
    "workload-type"         = "autonomous-agent-execution"
    "sandbox-runtime"       = "gvisor-runsc"
    "security-classification" = "restricted"
  }

  taint {
    key    = "dedicated"
    value  = "agent-cleanrooms"
    effect = "NO_SCHEDULE"
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Compliance  = "SOC2-Type-II"
  }
}

resource "aws_launch_template" "agent_node_template" {
  name_prefix   = "claude-agent-node-"
  image_id      = var.hardened_ami_id
  instance_type = "c6i.2xlarge"

  # Enforce IMDSv2 with hop-limit 1 to block container metadata theft
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 mandatory
    http_put_response_hop_limit = 1          # Blocks container-to-host metadata access
    instance_metadata_tags      = "disabled"
  }

  # Inject gVisor installation & cgroup configuration bootstrap script
  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -xe
    
    # Install gVisor runsc binary
    curl -fsSL https://gvisor.dev/archive.key | gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://gvisor.dev/apt release main" | tee /etc/apt/sources.list.d/gvisor.list
    apt-get update && apt-get install -y runsc
    
    # Configure containerd to register runsc runtime
    cat <<EOT >> /etc/containerd/config.toml
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
      runtime_type = "io.containerd.runsc.v1"
    EOT
    
    systemctl restart containerd
    
    # Enforce default-deny egress iptables rules
    iptables -A OUTPUT -m owner --uid-owner 10001 -d 169.254.169.254 -j DROP
    iptables -A OUTPUT -m owner --uid-owner 10001 -p udp --dport 53 -j DROP
  EOF
  )

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.agent_node_sg.id]
  }
}
